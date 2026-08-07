# Codex o'zgarishlar jurnali

Bu fayl Claude Code bilan parallel ishlashda Codex qilgan o'zgarishlarni kuzatish uchun yuritiladi.

## 2026-08-06 — Soddalashtirilgan tuzatish va qayta tahriz oqimi

- Raund raqami noto'g'ri "Tahrir #" bo'lib chiqqan barcha review belgilarining o'zbekcha nomi "Taqriz #"ga o'zgartirildi. Admin, muharrir va muallif sahifalarida bitta atama ishlaydi; ruscha "Рецензия #", inglizcha "Review #" ko'rinishida chiqadi. Oddiy tahrirlash (edit qilish) amallari bu o'zgarishga kirmaydi.
- Review jarayonidagi qolgan "tahriz" imlo xatosi ham "taqriz"ga tuzatildi: "Taqriz topshiriqlari", izoh/fayl/natija, muddat eslatmalari va xabarnomalar bir xil to'g'ri atamadan foydalanadi. "Tahrirchi" (muharrir) roli o'zgarishsiz qoldi.
- Bosh sahifadagi maqola kartasida muallifning ism-familiyasi endi bosiladigan havola: u `/articles?author_id=...` ga o'tib aynan shu muallifga tegishli barcha maqolalarni kartalar ko'rinishida chiqaradi. Muallif haqidagi hover-tooltip saqlanadi; qidiruv, saralash va sahifalash muallif filtrini ham saqlaydi. Bu havola umumiy maqolalar, son va maqola sahifalaridagi muallif nomlarida ham bir xil ishlaydi.
- Maxfiylik va interfeys tuzatishi: muharrirning matnli xulosasi faqat admin uchun qoladi, lekin muharrir biriktirgan tuzatish/markup fayli muallifga yuklab olish uchun beriladi. Muallifga admin yozgan tuzatish topshirig'i va tuzatish fayli chiqadi; oldingi jamlangan yozuvlarda ham `Muharrirlar izohi` matni xavfsiz yashiriladi.
- Muallifdagi tuzatish tarixi `Hal qilindi` emas, `Tuzatildi` deb ko'rsatiladi; tarixning yangi barcha yozuvlari o'zbek/rus/ingliz tillariga mos tarjima kalitlaridan foydalanadi.
- Adminning umumiy holat formasidagi izoh maydoni endi eski `submission.notes` bilan to'ldirilmaydi. Sahifa qayta ochilgach u bo'sh bo'ladi va yangi qaror uchun alohida izoh yoziladi.
- CKEditor yuborgan muharrir HTML-izohlari admin ko'rinishida endi `<p>` va `&#39;` kabi xom belgilar bilan emas, o'qilishi mumkin bo'lgan oddiy matn ko'rinishida chiqadi. Qayta-tahriz tizim yozuvi ham interfeys tiliga mos tarjima qilinadi.
- Tuzatish: antiplagiat natijasini `o'tdi` deb saqlashda 500 qaytishiga sabab bo'lgan `NameError: _parse_bool is not defined` bartaraf etildi. Boolean qiymatlarni o'qiydigan yordamchi funksiya `fmadmin/routes/web.py`ga qo'shildi; endi oddiy antiplagiat natijasi ham, tuzatilgan fayl uchun qayta antiplagiat natijasi ham bir xil xavfsiz yo'ldan o'tadi.
- Oldingi vaqtinchalik “kichik/katta tuzatish” va admin tanlaydigan qayta-tahriz oynasi bekor qilindi. Endi bitta tushunarli oqim ishlaydi: admin muallifga qaytaradi, muallif tuzatib yuboradi, tizim esa avvalgi muharrirlar uchun yangi raund (R2, R3, ...) topshiriqlarini avtomatik yaratadi.
- Oldingi topshiriq hech qachon qayta yozilmaydi: R1 taqrizi, tavsiyasi, fayli va sanalari tarixda qoladi; muallifning yangi fayli uchun yangi `pending` topshiriq yaratiladi. Admin jadvalidagi `Tahrir #` ustuni qaysi javob aynan qaysi versiyaga tegishli ekanini ko'rsatadi.
- Admin xohlasa, tuzatilgan joriy versiyaga `Tahrirchi biriktirish` orqali boshqa muharrirlarni ham qo'sha oladi. Ularning hammasi aynan bir raundga yoziladi.
- Muallifga qaytarishdan oldin tizim shu raunddagi faol muharrir topshiriqlari bor-yo'qligini tekshiradi. Faol topshiriq bo'lsa, admin barcha javoblarni kutishi yoki ortiqcha topshiriqni bekor qilishi kerak. Yakunlangan barcha anonim izohlar hamda fayllar muallif uchun bitta aniq topshiriqqa jamlanadi; har bir original taqriz admin tarixida alohida saqlanadi.
- Muharrirning `Rad etish tavsiyasi` maqolaning avtomatik rad etilishi emas. U faqat tavsiya: admin barcha R-raund javoblarini ko'rib, muallifga qaytarish, nashrga tavsiya qilish yoki yakuniy rad etish qarorini o'zi beradi. Avtomatik “nashrga tavsiya” faqat barcha joriy raund muharrirlari ijobiy xulosa yuborib, admin ularning barchasini qabul qilganda yuz beradi.
- Antiplagiat faqat admin “matn mazmuni sezilarli o'zgargan” deb aniq belgilaganda qayta talab qilinadi. Muallif yangi fayl yuborgach eski hisobot tozalanadi, yangi hisobot o'tgandan keyingina avtomatik qayta tahriz ochiladi. Boshqa holatda antiplagiatni yana bajarish shart emas.
- Agar antiplagiat muvaffaqiyatsiz bo'lib muallif yana tuzatsa, tizim bo'sh qolgan oraliq versiya sababli to'xtamaydi: eng oxirgi yakunlangan muharrirlar guruhini topib qayta topshiriq yaratadi.
- Admin sahifasida joriy tuzatilgan versiya uchun qisqa holat kartasi bor: antiplagiat kutilayotgani yoki faqat joriy `Tahrir #` javoblari qaror uchun ishlatilishi ko'rsatiladi. Muallif dashboardidagi tarixda esa bitta “tuzatish so'raldi” nomi, antiplagiat talabi va barcha muharrir fayllari ko'rinadi.
- Qo'shilgan migratsiya: `migrations/versions/20260806_000002_revision_review_workflow.sql`. U `revision_requires_antiplagiarism_recheck`, qayta-tekshiruv belgisi, jamlangan izohlar/fayllar va raund qidiruv indeksi qo'shadi. Lokal `journal2` bazasiga qo'llandi.
- Tekshiruv: Python kompilyatsiyasi, Jinja shablon sintaksisi, `git diff --check`, lokal baza ustunlari va Docker ichidagi mainweb/fmadmin workflow helper tekshiruvlari muvaffaqiyatli bajarildi. To'liq `pytest` konteynerda ham o'rnatilmagan (`pytest: executable file not found`).
- Tegilgan fayllar: mainweb/routes/api.py, mainweb/routes/dashboard.py, mainweb/templates/dashboard/articles.html, fmadmin/routes/web.py, fmadmin/templates/submissions/detail.html, fmadmin/templates/editors/review.html, migrations/versions/20260806_000002_revision_review_workflow.sql, db_schema.sql, tests/test_regressions.py, CODEX_CHANGES.md.

## 2026-08-06 — Tuzatilgan maqola fayllari tarixi

- Muallif tahrir qilib qayta yuborishidan oldin eski file_authors va file_anonymized fayllari submission_revision_log jadvaliga saqlanadi. Bu yuborish tugmasi avval saqlashidan kelib chiqadigan eski faylning yo'qolish muammosini bartaraf etadi.
- Eski fayllar endi admin maqolani tuzatishga qaytargan zahoti ham arxivlanadi. Natijada admin uchun har bir tahrir raqamiga mos eski fayl doim mavjud bo'ladi, muharrir esa faqat eng oxirgi anonim faylni oladi.
- submission_revision_log uchun fayl maydonlarini qo'shadigan migration yaratildi. Joriy fayl va tarixdagi fayllar endi alohida saqlanadi.
- Admin submission sahifasida joriy/yangi versiya, tahrir raqami va “Tuzatishdan oldingi versiyalar” ko'rsatiladi.
- Muharrir topshiriqlari ro'yxatida “Tuzatilgan versiya keldi” belgisi chiqadi; review sahifasiga esa faqat eng oxirgi tuzatilgan anonim fayl beriladi.
- Tarixiy fayllarni ochishdagi ruxsat tekshiruvi qo'shildi: avvalgi versiyalar va muallif ma'lumotli fayl faqat maqolaga ruxsati bor admin uchun ochiladi; muharrir faqat eng oxirgi anonimlashtirilgan faylni ochishi mumkin.
- Eski fayllarning snapshotda saqlanishi va yangi/oldingi versiyalar solishtirilishi uchun regression testlari qo'shildi.
- Tekshiruv: Python kompilyatsiyasi, Jinja shablon sintaksisi va git diff tekshiruvi muvaffaqiyatli bajarildi. To'liq pytest muhiti bu workspace'da o'rnatilmagan.
- Lokal journal2 bazasiga 20260806_000001_add_revision_file_history migratsiyasi qo'llandi va fmadmin hamda mainweb servislar qayta ishga tushirildi.
- Tegilgan fayllar: mainweb/routes/api.py, fmadmin/routes/web.py, fmadmin/templates/submissions/detail.html, fmadmin/templates/editors/review.html, fmadmin/templates/editors/assignments.html, migrations/versions/20260806_000001_add_revision_file_history.sql, db_schema.sql, tests/test_regressions.py, CODEX_CHANGES.md.

## 2026-08-06 — Dashboard status kartalarini filtrlashga ulash

- `fmadmin/templates/index.html` dagi har bir workflow/status kartasi endi `fmadmin/submissions?status=<status_kodi>` manziliga olib boradi.
- Mavjud submissions sahifasining serverdagi status filtri qayta ishlatildi; backendga alohida o'zgarish kiritilmadi.
- Kartalarga hover va klaviatura fokus holatlari qo'shildi, shunda ular bosiladigan element ekani ko'rinadi va klaviatura orqali ham ochiladi.
- Status URL'i uchun dashboard HTML render testi qo'shildi.
- Tekshiruv: Jinja shablon sintaksisi, Python kompilyatsiyasi va `git diff --check` muvaffaqiyatli bajarildi. To'liq `pytest` muhiti mavjud emas (`pytest` buyrug'i o'rnatilmagan).
- Tegilgan fayllar: `fmadmin/templates/index.html`, `tests/test_regressions.py`, `CODEX_CHANGES.md`.
