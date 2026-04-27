# FMADMIN - Aniq Ketma-Ketlikdagi Ish Rejasi

Bu hujjat noaniqliksiz, bajarish tartibida yozilgan amaliy plan.

## 0) Hozirgi holat

- [x] 1-bosqich: Global Search qo'shildi
- [x] 2-bosqich: Submissions Bulk Actions qo'shildi
- [x] 3-bosqich: Submissions Column Visibility qo'shildi
- [x] 4-bosqich: Keyboard shortcuts (Ctrl+K, Ctrl+Shift+S, Ctrl+Shift+U) qo'shildi
- [x] 5-bosqich: Auto Editor Assignment
- [x] 6-bosqich: Deadline reminders
- [x] 7-bosqich: Email Template Editor
- [x] 8-bosqich: 360 User Profile

---

## 1) Global Search (Bajarildi)

Maqsad: har sahifadan tez qidiruv.

Qilingan ishlar:
- Backend API: `GET /fmadmin/api/search`
- Navbar tugmasi + modal qidiruv oynasi
- Keyboard shortcut: `Ctrl+K`
- Qidiruv turlari: submissions, users, authors

Qabul mezoni:
- `Ctrl+K` bosilganda modal ochiladi
- 2+ belgi yozilganda natija chiqadi
- Natija bosilganda mos sahifaga o'tadi

---

## 2) Submissions Bulk Actions (Bajarildi)

Maqsad: bir nechta maqolani bir vaqtda boshqarish.

Qilingan ishlar:
- Jadvalga checkbox tanlash qo'shildi
- Select all qo'shildi
- Bulk form qo'shildi
- Backend endpoint: `POST /fmadmin/submissions/bulk`
- Amallar:
  - `set_submitted`
  - `set_in_process`
  - `set_published`
  - `set_rejected`

Qabul mezoni:
- 2 ta yoki undan ko'p maqola tanlab statusni o'zgartirish ishlaydi
- Tanlanmagan holatda xatolik ko'rsatadi

---

## 3) Column Visibility (Bajarildi)

Maqsad: jadvalni foydalanuvchi o'zi soddalashtirsin.

Qilingan ishlar:
- `Ustunlar` dropdown qo'shildi
- Muharrir, Yo'nalish, Admin, Tasnif, Muallif, Sana, Jarayon, Review ustunlari toggle qilinadi
- Tanlov `localStorage`da saqlanadi

Qabul mezoni:
- Ustunlarni yoqib/o'chirish darhol ishlaydi
- Sahifa refreshdan keyin ham tanlov saqlanib qoladi

---

## 4) Keyboard Shortcuts (Bajarildi)

Maqsad: tez navigatsiya.

Qilingan ishlar:
- `Ctrl+K` -> qidiruv
- `Ctrl+Shift+S` -> submissions sahifasi
- `Ctrl+Shift+U` -> users sahifasi

Qabul mezoni:
- Har uch shortcut ishlaydi

---

## 5) Auto Editor Assignment (Navbatdagi ish)

Maqsad: maqolani avtomatik ravishda mos muharrirga biriktirish.

Aniq ishlar:
1. `routes/web.py` ichida xizmat funksiyasi yozish:
   - track bo'yicha mos editorlarni topish
   - `editor_assignments` bo'yicha joriy yuklamani hisoblash
   - eng kam yuklamali editorga tanlash
2. `POST /fmadmin/submissions/<id>/auto-assign` endpoint qo'shish
3. Submission detail sahifasiga `Auto assign` tugmasi qo'shish
4. Log yozish (qaysi submission, qaysi editor)

Qabul mezoni:
- Tugma bosilganda mos editor avtomatik biriktiriladi
- Admin qo'lda override qila oladi

---

## 6) Deadline Reminders

Maqsad: muddat o'tishini oldindan eslatish.

Aniq ishlar:
1. `editor_assignments` deadline maydonlarini tekshirish
2. Har soat ishlaydigan reminder job yozish:
   - 24h qolganida
   - 6h qolganida
   - 1h qolganida
3. `role_notifications` ga yozish
4. Email yuborish (is_notify=true bo'lsa)

Qabul mezoni:
- Deadline yaqinlashganda admin va editor xabar oladi

---

## 7) Email Template Editor

Maqsad: xat matnlarini kodga kirmasdan tahrirlash.

Aniq ishlar:
1. `email_templates` jadvali qo'shish (migration)
2. CRUD sahifa: list/create/edit
3. Variables preview (`{{name}}`, `{{title}}`, ...)
4. `services/emailer.py` ni DB template bilan ishlaydigan qilish

Qabul mezoni:
- Template admin paneldan saqlanadi va email yuborishda ishlatiladi

---

## 8) 360 User Profile

Maqsad: foydalanuvchining barcha ma'lumoti bir joyda.

Aniq ishlar:
1. User detail sahifasiga bloklar qo'shish:
   - profil ma'lumotlari
   - submissions statistikasi
   - payments statistikasi
   - activity timeline
2. API yoki backend query optimizatsiyasi

Qabul mezoni:
- Bitta sahifada admin uchun to'liq ko'rinish ochiladi

---

## Ish tartibi (majburiy)

Har bosqich uchun:
1. Kod yoziladi
2. `get_errors` bilan tekshiriladi
3. Minimal smoke test qilinadi
4. Hujjatda status `[x]` qilinadi
5. Keyingi bosqichga o'tiladi

---

## Keyingi hozirgi qadam

Barcha bosqichlar yakunlandi. Endi faqat qo'shimcha polish va QA qoladi.
