# Tizim tahlili — qotib qolish va sekinlashish sabablari

**Sana:** 2026-08-06 (tashxis) / 2026-08-07 (tuzatishlar)
**Tahlil qildi:** Claude Code
**Holat:** ✅ 1, 2, 3, 5-muammolar tuzatildi — batafsili `CLAUDE_CHANGES.md` da

| # | Muammo | Holat |
|---|---|---|
| 1 | Bitta DB ulanishi + global qulf | ✅ Tuzatildi (thread-local ulanishlar) |
| 2 | `precheck()` 25s muzlash | ✅ Tuzatildi |
| 3 | 102 joyda qulfsiz `conn.cursor()` | ✅ Tuzatildi (avtomatik thread-safe) |
| 4 | SSE thread'larni band qiladi | 🟡 Yumshatildi (8 → 32 slot), tub yechim qolgan |
| 5 | Email sinxron (51s blok) | ✅ Tuzatildi (fon thread pool) |
| 6 | OAuth timeout | ❌ Noto'g'ri topilma — muammo yo'q edi |
| 7 | 21 ta N+1 so'rov | ⬜ Qolgan (baza kichik, hozir sezilmaydi) |

**Natija:** 16 parallel so'rov 0.555s → **0.273s** (~2× tez), bosh sahifa DB
tranzaksiyalari 13 → **2**.

---

## Qisqacha xulosa

Ilovada **ishlamay qoladigan (500) sahifa yo'q** — barcha asosiy endpointlar 200 qaytarmoqda,
loglarda ilova xatoligi yo'q. Muammo **arxitekturada**: butun tizim bitta DB ulanishi va bitta
global qulf (lock) orqali ishlaydi, shuning uchun foydalanuvchilar ko'paygan sayin hamma
navbatda turadi.

**O'lchangan isbot:**

| Holat | Javob vaqti |
|---|---|
| 1 ta so'rov (yolg'iz) | **12 ms** |
| 16 ta parallel so'rov | **200–530 ms** (~40 barobar sekin) |

16 ta parallel so'rov aniq **8 talik ikkita to'lqin** bo'lib keldi — bu `--threads 8` ga to'liq
mos keladi. Ya'ni tizim 8 tadan ortiq so'rovni bir vaqtda umuman qabul qila olmaydi.

---

## Muammolar (jiddiylik bo'yicha)

### 🔴 1. Bitta DB ulanishi + global qulf — HAMMA so'rov navbatda

**Fayl:** `mainweb/modules/connector.py:58` (va `fmadmin/connector.py` — nusxasi)

```python
def _sql(self, query, arguments, colnames = []):
    with self.connector._lock:      # <-- BUTUN ilovada BITTA qulf
        self.precheck()
        cursor = self.connection.cursor()
```

Butun ilovada bitta `psycopg2` ulanishi (`self.conn`) bor va har bir so'rov bitta
`threading.RLock()` orqali o'tadi. Ya'ni 8 ta thread bo'lsa ham, DB ishi **ketma-ket**
bajariladi — parallellik nolga teng.

**Oqibati:** foydalanuvchilar soni ortganda sayt eksponensial sekinlashadi.

---

### 🔴 2. `precheck()` qulf ostida 25 soniyagacha kutadi — to'liq muzlash

**Fayl:** `mainweb/modules/connector.py:36-55`

```python
def precheck(self, max_retries = 30):
    for attempt in range(max_retries):
        try:
            cursor.execute("SELECT 1;")
            ...
        except (OperationalError, InterfaceError):
            time.sleep(min(0.1 * (attempt + 1), 1.0))   # 30 marta!
            self.connector._connect()
```

Ikki alohida muammo:

**a) Har bir so'rovda ortiqcha yo'l.** Har bir haqiqiy so'rovdan **oldin** qo'shimcha
`SELECT 1` + `commit` yuboriladi. Bu DB ga borish-kelishni **ikki barobar** oshiradi.
O'lchov: bosh sahifa uchun 13 ta DB tranzaksiya — yarmi shu `SELECT 1`.

**b) Eng xavflisi — muzlash.** DB bilan ulanish bir lahzaga uzilsa, `precheck` 30 marta
qayta uriниб **25.5 soniya** kutadi — va bu vaqt davomida **global qulfni ushlab turadi**.
Natijada boshqa hamma thread bloklanadi → **butun sayt ~26 soniya qotadi**.

> Sizda kuzatilayotgan "qotib qolish" ning eng ehtimolli sababi shu.

---

### 🔴 3. 102 joyda qulfsiz `conn.cursor()` — ma'lumot yo'qolishi xavfi

Route'larda 102 ta joyda global qulfni **chetlab o'tib** to'g'ridan-to'g'ri umumiy
ulanishdan foydalaniladi:

```python
cursor = dbc.conn.cursor()      # qulf yo'q
...
dbc.conn.rollback()             # <-- boshqa thread'ning tranzaksiyasini ham bekor qiladi!
```

Bitta ulanish bir nechta thread tomonidan bo'lishilgani uchun A-thread'ning `rollback()`
chaqirig'i B-thread'ning saqlanmagan ishini ham yo'q qiladi.

**Alomatlari:** vaqti-vaqti bilan "saqlanmadi" holatlari, `current transaction is aborted`
xatoligi, tushuntirib bo'lmaydigan tasodifiy xatolar.

---

### 🟠 4. SSE (xabar oqimi) thread'larni band qilib turadi

**Fayllar:** `fmadmin/routes/messages.py:382, 512`, `mainweb/routes/messages.py`

4 ta SSE endpoint bor. Har biri:
- bitta thread'ni **110 soniya** ushlab turadi
- har **2 soniyada** DB ga so'rov yuboradi (global qulf orqali!)
- brauzer `EventSource` uzilganda **avtomatik qayta ulanadi** → thread abadiy band

**Hisob:**

| Muhit | Sozlama | Jami slot | Nechta ochiq xabar oynasi saytni qotiradi |
|---|---|---|---|
| Local | `--workers 1 --threads 8` | 8 | **8 ta** |
| Production | `--workers 4 --threads 12` | 48 | **48 ta** |

Ya'ni local'da 8 ta admin xabar sahifasini ochib qo'ysa — panel butunlay javob bermay qoladi.

*Eslatma:* nginx tomoni SSE uchun to'g'ri sozlangan (`proxy_buffering off`,
`proxy_read_timeout 3600s`) — muammo faqat gunicorn thread'larida.

---

### 🟠 5. Email so'rov ichida sinxron yuboriladi — 51 soniyagacha blok

**Fayl:** `shared/email/email_service.py:305-341`

- `MAIL_TIMEOUT = 15` soniya
- `max_retry_attempts = 3`
- Qayta urinish orasida kutish: 2s, 4s (eksponensial)

**Eng yomon holat:** 3 × 15s + 2s + 4s = **~51 soniya** bitta thread bloklanadi.

Faqat `fmadmin/routes/web.py` da **18 ta joyda** route ichida email yuboriladi. SMTP sekin
ishlasa, admin "Saqlash" tugmasini bosib 51 soniya kutadi va shu payt bitta thread yo'qoladi.

---

### ~~🟡 6. OAuth so'rovlarida timeout yo'q~~ — ❌ NOTO'G'RI TOPILMA

Dastlab `mainweb/routes/auth.py:2112, 2533` da timeout yo'qdek ko'ringan edi. Bu **xato**
xulosa bo'ldi — grep ko'p qatorli chaqiruvlarni noto'g'ri o'qigan.

AST orqali qayta tekshirildi: loyihadagi **barcha** `requests.*` chaqiruvlarida `timeout`
mavjud. Bu yerda muammo yo'q, hech narsa o'zgartirilmadi.

---

### 🟡 7. Route'larda 21 ta N+1 so'rov

Sikl ichida `.exec()` chaqirilgan joylar — masalan `mainweb/routes/public.py:4495`
(har bir hammuallif uchun alohida so'rov), `fmadmin/routes/web.py:12040`.

Hozircha baza kichik (submissions: 27, users: 22 qator) bo'lgani uchun sezilmaydi, lekin
har bir so'rov global qulfdan o'tgani uchun **kelajakda tez o'sadi**.

---

## Yaxshi tomonlari (muammo yo'q)

- ✅ Indekslar to'liq qo'yilgan (`submissions`, `publications`, `editor_assignments`, `messages`)
- ✅ Baza kichik va sog'lom, sekin so'rov yo'q (median 1ms)
- ✅ nginx SSE uchun to'g'ri sozlangan
- ✅ Loglarda ilova xatoligi (traceback/500) yo'q
- ✅ Barcha asosiy sahifalar 200 qaytarmoqda

---

## Tavsiya etilgan yechimlar (tartib bo'yicha)

| # | Yechim | Ta'sir | Mehnat | Xavf |
|---|---|---|---|---|
| 1 | `precheck()` retry'ni 30 → 2 ga tushirish, qulf tashqarisiga chiqarish | 🔴 26s muzlash yo'qoladi | 30 daqiqa | Past |
| 2 | `ThreadedConnectionPool` (har thread'ga alohida ulanish) | 🔴 Parallellik tiklanadi, #1/#3 birdan hal bo'ladi | 1 kun | O'rta |
| 3 | Email'ni fonga (background thread/queue) o'tkazish | 🟠 51s blok yo'qoladi | 2-3 soat | Past |
| 4 | OAuth `requests` ga `timeout=10` qo'shish | 🟡 Cheksiz osilish yo'qoladi | 10 daqiqa | Juda past |
| 5 | SSE: poll oralig'ini 2s → 5s, yoki `gevent` worker'ga o'tish | 🟠 Thread tanqisligi yumshaydi | 2 soat / 1 kun | O'rta |
| 6 | Local'da `--threads 8` → `--threads 24` | 🟠 Vaqtinchalik yengillik | 2 daqiqa | Juda past |
| 7 | N+1 larni birlashtirilgan so'rovga aylantirish | 🟡 Kelajak uchun | 1 kun | Past |

### Eng tez yengillik (bugun, ~1 soat)

1, 4 va 6 — bularni birga qilsa: 26 soniyalik muzlashlar yo'qoladi, OAuth osilishi tugaydi,
thread tanqisligi 3 barobar yumshaydi. Kod arxitekturasiga tegilmaydi, xavf minimal.

### Asosiy yechim (keyingi qadam)

№2 — connection pool. Bu #1, #2a va #3 muammolarni **bir yo'la** hal qiladi va tizim
haqiqiy parallel ishlay boshlaydi. Lekin `connector.py` ning yuragiga tegadi, shuning uchun
alohida branch va sinchkov test talab qiladi.
