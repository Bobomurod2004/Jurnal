# Claude Code o'zgarishlar jurnali

Bu fayl Codex bilan parallel ishlashda Claude Code qilgan o'zgarishlarni kuzatish uchun yuritiladi.
(Codex o'z jurnalini `CODEX_CHANGES.md` da yuritadi.)

---

## 2026-08-06 — Administrator rollarini kengaytirish (RBAC bo'linishi)

### Maqsad

Administrator (`admin`) roli faqat arizalar va tayinlovlar bilan cheklangan edi. Endi u
kundalik jurnal operatsiyalarini ham bajaradi: jurnal kontenti, muharrir qo'shish va
kelgan to'lovlarni tasdiqlash. Saytning "kritik" qismlari (narx siyosati, sayt matnlari,
foydalanuvchi rollari) superadmin'da qoldi.

### Muammo

`fmadmin.content.manage` bitta ruxsat sifatida jurnal kontenti + sayt boshqaruvi + email +
moliya menyusining hammasini qamrab olgan edi. Uni bo'lmasdan turib admin'ga faqat jurnal
kontentini berib bo'lmasdi. Shuning uchun ruxsat bitta emas, bir nechta aniq ruxsatga
ajratildi.

### Yakuniy ruxsat matritsasi

| Permission | Ochadigan sahifa/amal | superadmin | admin | editor |
|---|---|:---:|:---:|:---:|
| `fmadmin.content.manage` | Sonlar, Maqolalar (yaratish/tahrirlash), Yangiliklar, E'lonlar | ✅ | ✅ **yangi** | ❌ |
| `fmadmin.content.delete` | Son o'chirish, Maqola o'chirish | ✅ | ❌ | ❌ |
| `fmadmin.editors.manage` | Muharrirlar: qo'shish / tahrirlash / o'chirish | ✅ | ✅ **yangi** | ❌ |
| `fmadmin.payments.manage` | To'lovlar ro'yxati + tasdiqlash/rad etish | ✅ | ✅ **yangi** | ❌ |
| `fmadmin.site.manage` | Sahifalar, Bosh sahifa video/rasm, Aloqa, Tarjimalar, Email shablon/loglar | ✅ | ❌ | ❌ |
| `fmadmin.finance.manage` | Tariflar, To'lov yo'riqnomasi (narx siyosati) | ✅ | ❌ | ❌ |
| `fmadmin.users.manage` | Foydalanuvchilar, Mualliflar, Tahrir hay'ati | ✅ | ❌ | ❌ |
| `fmadmin.assignments.manage` | Tayinlovlar | ✅ | ✅ *(avvaldan bor)* | ❌ |

**Asos:** kelgan to'lovni tasdiqlash — kundalik operatsion ish (admin), lekin narx belgilash —
siyosat (superadmin). Xuddi shunday: maqolani tahrirlash operatsion, nashr etilganini
o'chirish esa qaytarib bo'lmaydigan amal (superadmin).

### Tegilgan fayllar

| Fayl | O'zgarish |
|---|---|
| `fmadmin/utils/roles.py` | 4 ta yangi permission; `admin` roliga 3 tasi berildi; `CAPABILITY_PERMISSION_MAP` ga 4 ta yangi capability |
| `mainweb/utils/roles.py` | `fmadmin/utils/roles.py` ning aynan nusxasi (loyihada shunday yuritiladi) |
| `fmadmin/utils/auth.py` | `permission_required(*names)` — web sahifalar uchun; `api_any_permission_required(names)` — bir nechta bo'limga tegishli API uchun |
| `fmadmin/routes/web.py` | 44 ta route dekoratori almashtirildi; `_actor_may_manage_staff_account()` himoyasi qo'shildi |
| `fmadmin/routes/api.py` | `api_site_required`, `api_author_picker_required` qo'shildi; tarjima API'lari `site.manage` ga o'tdi |
| `fmadmin/hooks.py` | Kontekst protsessoriga `user_caps` global qo'shildi |
| `fmadmin/templates/basic.html` | Sidebar guruhlari yangi capability'lar bo'yicha bo'lindi |
| `fmadmin/templates/website/issues/issues.html` | "O'chirish" tugmasi `can_delete_content` bilan yashirildi |
| `fmadmin/templates/website/articles/articles.html` | "O'chirish" tugmasi `can_delete_content` bilan yashirildi |
| `tests/test_role_permissions.py` | **Yangi fayl** — 17 ta regression test |
| `tests/test_regressions.py` | Faqat `ADMIN_CAPABILITIES` dict'iga yangi kalitlar qo'shildi (Codex'ning ishiga tegilmadi) |

### Route dekoratorlari (44 ta almashtirildi)

`@is_superadmin_required` → aniq ruxsat dekoratorlariga:

- `content_required` (9): `/fmadmin/website/issues`, `.../issues/<id>`, `/fmadmin/website/articles`,
  `.../articles/<id>`, `.../articles/<id>/content`, `/fmadmin/website/news`, `.../news/edit/<id>`,
  `/fmadmin/website/announcements`, `.../announcements/edit/<id>`
- `content_delete_required` (2): `.../issues/<id>/delete`, `.../articles/<id>/delete`
- `editors_required` (3): `/fmadmin/editors`, `.../editors/<id>`, `.../editors/<id>/delete`
- `payments_required` (2): `/fmadmin/finance/payments`, `.../payments/edit`
- `finance_required` (2): `/fmadmin/website/tariffs`, `/fmadmin/website/payment-guide`
- `site_required` (15): pages, home-videos, home-gallery, contact-info, translations, email-templates, email-logs
- `users_required` (11): users, authors, editorial-members

### Xavfsizlik

1. **Rol ko'tarilishiga qarshi himoya.** `editor_edit` da yangi muharrir yaratilganda
   `rolename='editor'` qattiq yozilgan — admin o'ziga yoki boshqaga admin/superadmin roli
   bera olmaydi.
2. **Yon tomondan ko'tarilishga qarshi himoya (yangi).** `_actor_may_manage_staff_account()`:
   superadmin bo'lmagan aktor `admin`/`superadmin` rolli hisobni tahrirlay/o'chira olmaydi.
   Bu superadmin'da `editor` roli ham bo'lgan holatni yopadi. Uch joyda qo'llanadi:
   `editors()` ro'yxati (bunday hisoblar ro'yxatdan ham chiqarib tashlanadi), `editor_edit()`
   (GET va POST), `editor_delete()`.
3. **Menyu va tugmalar.** Ruxsati yo'q havola umuman ko'rsatilmaydi — "ruxsat yo'q" sahifasiga
   olib boradigan tugma yomonroq tajriba.

### Muhim texnik qaror: `user_caps` global

`basic.html` dagi `{% set user_caps = ... %}` Jinja'da **bola shablonning `{% block %}` ichida
ko'rinmaydi**. Shuning uchun `user_caps` `hooks.py` kontekst protsessoriga global sifatida
qo'shildi — nomi `basic.html` dagi bilan **bir xil** qilib qoldirildi, shunda ikkita nom
bo'lmaydi va mavjud testlar buzilmaydi. Endi istalgan shablon `user_caps.can_*` ni o'qiy oladi.

### Migratsiya

**Kerak emas.** Ruxsatlar koddan hisoblanadi, DB'da saqlanmaydi. Sessiya `hooks.py` dagi
`before_request` da har so'rovda DB'dan qayta hisoblanadi — mavjud adminlar qayta login
qilmasdan yangi huquqni oladi.

### CSS

Tegilmadi. Faqat `fmadmin` shablonlari o'zgardi (Tabler UI), `mainweb` Tailwind manbasiga
tegilmagani uchun `npm run build:css` kerak emas.

### Tekshiruv

- `.venv-test/bin/pytest tests/` → **142 passed** (shundan 17 tasi yangi)
- `python3 -m py_compile` — barcha o'zgargan Python fayllari
- Codex tegayotgan fayllar (`fmadmin/templates/index.html`) ga tegilmadi;
  `tests/test_regressions.py` da faqat bitta dict kengaytirildi

### Qo'lda tekshirish uchun

Test admin hisobi bilan kiring va quyidagini kuting:

| Sahifa | admin | superadmin |
|---|---|---|
| `/fmadmin/website/issues`, `/articles`, `/news`, `/announcements` | ochiladi | ochiladi |
| Son/Maqola ro'yxatidagi "O'chirish" tugmasi | ko'rinmaydi | ko'rinadi |
| `/fmadmin/editors` | ochiladi | ochiladi |
| `/fmadmin/finance/payments` | ochiladi, status o'zgartirsa bo'ladi | ochiladi |
| `/fmadmin/website/tariffs` | menyuda yo'q, to'g'ridan-to'g'ri kirsa — bosh sahifaga qaytaradi | ochiladi |
| `/fmadmin/users/users`, `/authors`, `/editorial-members` | menyuda yo'q, kirib bo'lmaydi | ochiladi |
| `/fmadmin/website/pages`, `/translations`, `/email-logs` | menyuda yo'q, kirib bo'lmaydi | ochiladi |

---

## 2026-08-07 — Unumdorlik: muzlash sabablarini bartaraf etish

To'liq tashxis: `PERFORMANCE_ANALYSIS.md`. Quyida amalga oshirilgan tuzatishlar.

### 1. `_sql()` — 25 soniyalik muzlash olib tashlandi

**Fayllar:** `mainweb/modules/connector.py`, `fmadmin/connector.py` (ikkalasi bir xil)

Ilgari har bir so'rov global qulf ostida `precheck()` ni chaqirardi, u esa:
- har safar ortiqcha `SELECT 1` + `commit` yuborardi (DB borish-kelishi 2 barobar)
- ulanish uzilsa **30 marta** qayta urinib, **25.5 soniya** kutardi — va bu vaqt davomida
  global qulfni ushlab turardi, ya'ni **butun ilova muzlardi**

Endi:
- Ortiqcha `SELECT 1` yo'q. Ulanish holati `connection.closed` (lokal maydon, DB ga
  bormaydi) orqali tekshiriladi.
- Ulanish uzilsa bir marta qayta ulanadi.
- **Faqat o'qish so'rovlari** qayta yuboriladi (`SELECT/COUNT/SUMM/GROUP_BY`). Yozuv
  so'rovi qayta yuborilmaydi — server uzilishdan oldin commit qilgan bo'lishi va yozuv
  ikki marta tushishi mumkin.

**O'lchandi:** bosh sahifa uchun DB tranzaksiya soni **13 → 2**.

### 2. Email fonga o'tkazildi

**Yangi fayl:** `shared/email/background.py` — kichik thread pool (`MAIL_BACKGROUND_WORKERS`,
default 4). Worker `app_context()` ochadi, chunki email shablonlari app'ning Jinja
muhitidan render qilinadi (ular `request`/`session` ga tegmaydi — tekshirildi).

Ikkala wrapper'ga (`mainweb/utils/emailer.py`, `fmadmin/services/emailer.py`)
`background=False` parametri qo'shildi.

**Fonga o'tkazilganlar** (qaytish qiymati hech qayerda ishlatilmaydi — tekshirildi):
- `fmadmin/routes/web.py:_send_user_email` — admin panelidagi **barcha** bildirishnomalar
- `mainweb/routes/api.py:_send_user_email` — to'lov/ariza bildirishnomalari
- `mainweb/routes/public.py` — kontakt formasi tasdig'i (foydalanuvchiga)

**Ataylab sinxron qoldirildi:**
- `mainweb/routes/auth.py` — tasdiqlash kodlari (foydalanuvchi kutib turadi, xatolikni
  ko'rsatish shart)
- `mainweb/routes/public.py` — kontakt formasining admin nusxasi (`fail_silently=False`,
  xatolik foydalanuvchiga flash orqali bildiriladi va murojaat DB ga saqlanmaydi)

**Jonli sinov:** kontakt formasi → javob **69 ms**, Mailpit'ga 3 ta xat yetib bordi
(2 ta sinxron admin + 1 ta fon rejimidagi tasdiq).

### 3. Gunicorn thread soni

`docker-compose.local.yml`: 8 → **16**, `docker-compose.yml`: 12 → **16**.

**Halol eslatma:** bu **tezlik uchun emas**. Nazorat ostidagi A/B o'lchov:

| Threads | 16 parallel so'rov |
|---|---|
| 8 | 0.618s |
| 16 | 0.629s |
| 24 | 0.780s |

Ya'ni thread qo'shish **yordam bermaydi** — hammasi baribir bitta global qulfda navbat
kutadi, ustiga kontekst almashinuvi qo'shiladi. 16 tanlandi chunki u 8 ga teng ishlaydi,
lekin SSE (xabar oqimi) uchun **2 barobar zaxira** beradi: SSE thread'lari asosan uxlaydi,
qulf uchun kurashmaydi, shuning uchun ularga slot kerak.

Takroriy o'lchovlarda tarqalish katta (bir xil sozlamada 0.62–0.99s), shuning uchun
**throughput yaxshilandi deb ayta olmayman**. Aniq isbotlangani — DB borish-kelishlari
ikki barobar kamaydi va 25 soniyalik muzlash yo'qoldi.

### Tegilgan fayllar

`mainweb/modules/connector.py`, `fmadmin/connector.py`, `shared/email/background.py` (yangi),
`mainweb/utils/emailer.py`, `fmadmin/services/emailer.py`, `mainweb/routes/api.py`,
`mainweb/routes/public.py`, `fmadmin/routes/web.py`, `docker-compose.local.yml`,
`docker-compose.yml`

### Tekshiruv

- `pytest tests/` → **149 passed, 1 failed**. Yiqilgan test —
  `test_compute_revision_reentry_...`, u **Codex'ning** `mainweb/routes/api.py` dagi
  o'zgarishiga tegishli (men bu funksiyaga tegmadim). Tegilmadi.
- Barcha servislar sog'lom: mainweb/fmadmin `/healthz` 200, nginx 200.

### Keyingi qadam (hali qilinmadi)

**Connection pool** — asosiy yechim. Hozir butun ilova **bitta** DB ulanishi va **bitta**
global qulf orqali ishlaydi, shuning uchun parallellik nolga teng. Bundan tashqari 102 ta
joyda qulfsiz `conn.cursor()` ishlatiladi — bitta thread'ning `rollback()` i boshqasining
saqlanmagan ishini o'chiradi.

Tavsiya: `conn` ni **thread-local** qilish. Bu bir yo'la uchala muammoni hal qiladi va
102 ta chaqiruv joyini o'zgartirishni talab qilmaydi.

⚠️ **Diqqat:** PostgreSQL `max_connections = 100`. Production'da 4 worker × 2 servis = 8
protsess; har biriga 16 thread'dan ulanish berilsa 128 bo'lib limitdan oshadi. Pool
o'lchamini cheklash yoki `max_connections` ni oshirish kerak.

> ✅ Bajarildi — pastdagi bo'limga qarang.

---

## 2026-08-07 (2) — Thread-local DB ulanishlari: global qulf olib tashlandi

Yuqoridagi "keyingi qadam" amalga oshirildi.

### O'zgarish

**Fayllar:** `mainweb/modules/connector.py`, `fmadmin/connector.py`

Ilgari butun ilovada **bitta** `psycopg2` ulanishi bor edi va har bir so'rov
`threading.RLock()` orqali o'tardi — ya'ni 16 thread bo'lsa ham DB ishi ketma-ket
bajarilardi.

Endi `PostgreSQLConnector.conn` — **property**, u chaqirayotgan thread'ning **o'z**
ulanishini qaytaradi (birinchi murojaatda ochiladi, `threading.local()` da saqlanadi).

Shuning natijasida:

1. **`_sql()` dan global qulf olib tashlandi** — thread'lar endi haqiqatan parallel ishlaydi.
2. **Cross-thread `rollback()` bug'i yo'qoldi.** Ilgari bitta ulanish bo'lishilgani uchun
   A-thread'ning `rollback()` i B-thread'ning saqlanmagan ishini o'chirardi. Endi har
   thread o'z tranzaksiyasida.
3. **102 ta raw `dbc.conn.cursor()` joyi o'zgartirilmadi** — ular avtomatik thread-safe
   bo'lib qoldi, chunki `.conn` endi thread'ning o'zinikini qaytaradi.
4. **`pg_advisory_xact_lock` endi to'g'ri ishlaydi.** Ilgari hamma thread bitta sessiyada
   edi, shuning uchun tranzaksiya-doirasidagi advisory lock thread'lar orasida deyarli
   ma'nosiz edi. Endi har thread alohida sessiya — lock haqiqatan himoya qiladi.

`ConnectorQuery.connection` ham property qilindi (`self.connector.conn`), shunda bir
thread'da yaratilgan query obyekti boshqa thread'da bajarilsa ham to'g'ri ulanishga tegadi.

`self._lock` atributi **saqlab qolindi** — route'larda 7 joyda (`with dbc._lock:`)
ishlatiladi, olib tashlansa AttributeError beradi.

### Ulanish byudjeti

Har thread bitta ulanish ushlaydi, shuning uchun `max_connections` oshirildi:

```yaml
command: ["postgres", "-c", "max_connections=300"]
```

Production hisobi: 4 worker × 16 thread × 2 servis = **128** + monitoring. Default 100
yetmasdi.

### Worker soni (local)

Nazorat ostidagi o'lchov ko'rsatdiki, qulf olib tashlangandan keyin ham **bitta protsess
ichida** throughput ~34 req/s da to'yinadi — bu GIL cheklovi. Worker'ni 2 ga oshirish
53.6 req/s berdi. Shuning uchun local'da mainweb va fmadmin **`--workers 2`** qilindi
(production allaqachon 4 worker).

### O'lchangan natija

| Ko'rsatkich | Boshida | Hozir |
|---|---|---|
| 16 parallel so'rov | 0.555s (~29 req/s) | **0.273s (~58.6 req/s)** |
| 32 parallel so'rov | — | 0.561s (~57 req/s) |
| Bosh sahifa DB tranzaksiyalari | 13 | **2** |
| Eng yomon muzlash (DB uzilishi) | ~25.5s | bir marta qayta ulanish |
| DB ulanishlari | 1 (hammaga) | 45 / 300 |

### Tekshiruv

- `pytest tests/` → **149 passed, 1 failed** (o'sha Codex'niki, o'zgarmadi)
- Barcha sahifalar 200: `/`, `/articles`, `/issues`, `/editorial`, `/login`, `/fmadmin/`
- Yozuv oqimi jonli sinaldi: kontakt formasi → 302, Mailpit'ga 3 ta xat
- DB konteyneri qayta yaratildi; ma'lumot butun qoldi (users=21, submissions=27,
  publications=3, translations=1178 — oldin va keyin bir xil)

### Qolgan ishlar (hali qilinmadi)

- **21 ta N+1 so'rov** route'larda (`PERFORMANCE_ANALYSIS.md` §7). Baza kichik bo'lgani
  uchun hozir sezilmaydi.
- **SSE thread'lari** hali ham 110 soniya slot ushlaydi. Endi 2 worker × 16 thread = 32
  slot (ilgari 8), lekin tub yechim — `LISTEN/NOTIFY` yoki `gevent` worker.
- Production'da `max_connections=300` uchun PostgreSQL xotirasi tekshirilishi kerak
  (har ulanish ~5-10 MB work_mem talab qilishi mumkin).

---

## 2026-08-07 (3) — Uchta xatolik: vaqt zonasi, admin yo'nalishlari, Grafana

### 1. Muharrir biriktirishda noto'g'ri vaqt olinardi

**Sabab.** Vaqtlar UTC epoch sifatida saqlanadi. Ko'rsatish filtrlari
(`utils/filters.py`) UTC+5 qo'shardi, lekin formadan **qaytib o'qishda** hech narsa
ayirilmasdi — `datetime.strptime(...).timestamp()` serverning soatiga (UTC) qarab
o'qirdi. Natijada admin **14:00** tanlasa, tizim **19:00** ni saqlardi.

Bundan tashqari forma standart qiymatlari (`min`, `max`, `value`) ham UTC da
to'ldirilardi — ya'ni ochilganda ham 5 soat orqada ko'rsatardi.

**Yechim.** `fmadmin/utils/filters.py` ga bitta manba qilib qo'yildi:

- `parse_ui_datetime(value)` — naive qiymatni **Toshkent devor soati** deb o'qiydi
  (`calendar.timegm(...) - UI_TZ_OFFSET_SECONDS`)
- `parse_ui_date(value, end_of_day=)`
- `ui_datetime_input_value(ts)` — epoch → `datetime-local` qiymati

`fmadmin/routes/web.py` da `_parse_datetime_to_timestamp` va
`_parse_date_to_timestamp` shu yordamchilarga o'tkazildi; biriktirish formasidagi
`min/max/default` qiymatlar ham shular orqali yasaladi.

Offset `UI_TZ_OFFSET_HOURS` env orqali sozlanadi (default 5).

**Tekshirildi:** admin `2026-08-10 14:00` kiritsa → bazada `09:00 UTC`, ekranda
yana `10.08.2026 14:00`.

### 2. Admin yo'nalishlari (magistr / o'qituvchi / doktorant)

**Sabab — kod emas, konfiguratsiya + ko'rinmaslik.** Mexanizm to'g'ri ishlayapti
(forma, JS, `_realign_submission_admin_assignments` — hammasi joyida). Lekin
bazada:

| Yo'nalish | Arizalar | Biriktirilgan admin |
|---|---|---|
| `masters` | 16 | ✅ 12 va 13-adminlar |
| `phd` | 4 | ❌ **hech kim** |
| `teacher` | 2 | ❌ **hech kim** |

Ikkala adminda ham faqat `{masters}` bor edi. Yo'nalishni hech kim qoplamasa,
`_realign_...` arizani jimgina biriktirmasdan qoldiradi — **hech qayerda
ogohlantirish yo'q**, shuning uchun 6 ta ariza ko'rinmay osilib qolgan.

**Yechim.** `_uncovered_admin_tracks()` qo'shildi va foydalanuvchilar sahifasida
sariq ogohlantirish chiqadi:

> **Yo'nalishsiz arizalar bor** — Doktorantura: 4 ta ariza kutmoqda,
> O'qituvchi: 2 ta ariza kutmoqda

Eski yozilishlar (`magistr`, `doktorant`, ...) alias orqali to'g'ri hisoblanadi.
DB xatoligi bo'lsa sahifa yiqilmaydi — ogohlantirish shunchaki ko'rsatilmaydi.

> ⚠️ **Sizdan talab qilinadi:** `/fmadmin/users/users` ga kirib, kerakli adminni
> tahrirlang va "Admin yo'nalishlari" dan **Doktorantura** va **O'qituvchi** ni
> belgilang. Men real admin hisoblariga tegmadim.

### 3. Grafana serverda to'liq faollashmasligi

**Sabablar.**

1. `GF_SERVER_ROOT_URL` `http://127.0.0.1:3000` ga **qattiq yozilgan** edi. Brauzerda
   boshqa manzildan ochilsa, Grafana yuklanadi-yu, redirect va asset havolalari
   `127.0.0.1` ga ishora qiladi — "yarim ishlaydi" holati aynan shu.
2. Port `127.0.0.1:3000` ga bog'langan va nginx'da `/grafana/` marshruti **yo'q** edi
   — ya'ni tashqaridan umuman ochib bo'lmasdi.
3. `GRAFANA_ADMIN_PASSWORD` `:?` bilan majburiy — `.env` da bo'lmasa butun
   observability stack **ishga tushmaydi**.

**Yechim.**

- `docker-compose.observability.yml`: `GF_SERVER_ROOT_URL` → `${GRAFANA_ROOT_URL:-...}`,
  qo'shimcha `GF_SERVER_SERVE_FROM_SUB_PATH`
- `nginx/nginx.conf`: `/grafana/` marshruti qo'shildi — sayt TLS'i orqali, WebSocket
  (Grafana Live) qo'llab-quvvatlanadi. Upstream **lazy DNS** orqali hal qilinadi
  (`resolver 127.0.0.11` + `set $grafana_upstream`), shuning uchun observability
  stack o'chiq bo'lsa ham **nginx ishga tushaveradi**
- `.env.production.example` va `README.md` — ikkala variant (nginx orqali yoki
  to'g'ridan-to'g'ri port) hujjatlashtirildi

**Tekshirildi:** `nginx -t` → `configuration file test is successful`.

> ⚠️ **Serverda qilinadigan ish:** `.env` ga qo'shing:
> ```
> GRAFANA_ADMIN_PASSWORD=<kuchli parol>
> GRAFANA_ROOT_URL=https://<domeningiz>/grafana/
> GRAFANA_SERVE_FROM_SUB_PATH=true
> ```
> so'ng: `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d`
> va nginx'ni qayta yuklang.

### Tegilgan fayllar

`fmadmin/utils/filters.py`, `fmadmin/routes/web.py`,
`fmadmin/templates/users/users/users.html`, `nginx/nginx.conf`,
`docker-compose.observability.yml`, `.env.production.example`, `README.md`,
`tests/conftest.py`, `tests/test_admin_workflow_fixes.py` (yangi)

`tests/conftest.py` da `utils.filters` aliasi endi ikkala ilovadan birlashtiriladi
(avval faqat mainweb'dan olinardi, shuning uchun yangi yordamchilar topilmasdi) —
bu `utils.roles`, `utils.auth` uchun allaqachon qo'llanilgan naqsh.

### Tekshiruv

- `pytest tests/` → **163 passed, 1 failed** (14 tasi yangi). Yiqilgan test hamon
  Codex'niki (`_compute_revision_reentry`) — tegilmadi.
- `nginx -t` muvaffaqiyatli (soxta sertifikat bilan, journal tarmog'ida)
- fmadmin qayta ishga tushirildi: `/healthz` 200, loglarda 0 ta xatolik

---

## 2026-08-07 (4) — Yo'nalish izolyatsiyasi: har admin faqat o'z maqolalarini ko'radi

### Muammo

Doktorantura belgilangan admin `phd` maqolalarni to'g'ri ko'rardi, **lekin yo'nalishi
ko'rsatilmagan maqolalarni ham ko'rardi**. Haqiqiy baza bilan simulyatsiya:

```
=== Doktorantura admini (tuzatishdan OLDIN) ===
  (YO'NALISHSIZ)   4 ta   <- ko'rmasligi kerak
  phd              4 ta   <- to'g'ri
```

**Sabab.** `_user_has_track_access()` yo'nalish bo'sh bo'lsa `True` qaytarardi:

```python
normalized_track = _normalize_admin_track(track)
if not normalized_track:
    return True          # <-- har qanday admin ko'raverardi
```

Bu `_can_access_submission()` ning zaxira yo'lida ishlaydi (ariza hali hech kimga
biriktirilmagan holat). Natijada egasiz + yo'nalishsiz 4 ta ariza **hamma
adminlarga** ko'rinardi — bu yo'nalish tayinlashning ma'nosini yo'qqa chiqaradi.

### Yechim

`_user_has_track_access()` endi yo'nalish bo'sh bo'lsa `False` qaytaradi: yo'nalishsiz
ariza hech qaysi adminning navbatiga tegishli emas, u superadminda qoladi.

Bunday arizalar unutilib qolmasligi uchun `_untracked_submission_count()` qo'shildi va
foydalanuvchilar sahifasida ko'k xabar chiqadi:

> **Yo'nalishi ko'rsatilmagan 4 ta ariza** — ular faqat superadminga ko'rinadi.

`_can_access_submission()` butun fmadmin bo'ylab **17 ta joyda** ishlatiladi (ro'yxat,
tafsilot, fayllar, amallar), shuning uchun tuzatish hamma joyda bir xil ta'sir qildi.

### Tuzatishdan KEYINGI natija (haqiqiy baza bilan tekshirildi)

| Kim | Ko'radi |
|---|---|
| Doktorantura admini | faqat `phd` — 4 ta |
| O'qituvchi admini | faqat `teacher` — 2 ta |
| Magistratura admini (id=12) | faqat o'ziga biriktirilgan `masters` — 8 ta |
| Superadmin | hammasi — 26 ta (shu jumladan 4 ta yo'nalishsiz) |

### Yo'naltirish (allaqachon ishlayapti)

Yangi ariza yuborilganda `mainweb/routes/api.py:_pick_assigned_admin_id()` yo'nalishga
mos adminlardan **eng kam yuklanganini** tanlab biriktiradi. Ya'ni "unga borib tushishi"
qismi kod darajasida tayyor — faqat `phd`/`teacher` yo'nalishlariga admin belgilash
kerak (yuqoridagi 2-bo'limga qarang).

### Tegilgan fayllar

`fmadmin/routes/web.py`, `fmadmin/templates/users/users/users.html`,
`tests/test_admin_workflow_fixes.py`

### Tekshiruv

- `pytest tests/` → **171 passed, 1 failed** (22 tasi yangi). Yiqilgan test hamon
  Codex'niki.
- Haqiqiy baza bilan simulyatsiya qilindi (yuqoridagi jadval)
- fmadmin qayta ishga tushirildi: `/healthz` 200, loglarda 0 ta xatolik
