# Reja: Antiplagiat workflow + Chat + Revizor jarayoni

## QISM A — Antiplagiat + Chat (amalga oshirilgan, ishlayapti — tegilmaydi)

- Admin antiplagiat faylini o'zi yuklay oladi (mualif o'rniga), natijasini (o'tdi/o'tmadi) belgilaydi, sabab bilan.
- Mualif dashboardida kim yuklagani (admin/mualif) va natija ko'rinadi.
- Muharrir biriktirish (auto-assign / assign-editors) faqat antiplagiat "o'tdi" deb belgilangandan keyin ochiladi.
- Yangi status: `antiplagiarism_failed` — antiplagiatdan o'tmasa, maqola mualifga qaytadi, u tuzatib qayta yuklaydi.
- Chat (mualif↔admin, admin↔muharrir) ga fayl/rasm biriktirish qo'shilgan.

## QISM B — Revizor jarayoni (amalga oshirilgan, ishlayapti — tegilmaydi)

**Muammo edi**: har qanday qaytarishda (kichik imlo xatosimi, jiddiy kamchilikmi — farqsiz) butun tahrirchilar qayta biriktirilib, taqriz 0dan boshlanardi. Muharrir "muallifga qaytarish" qilganda uning fayli mualif dashboardida bitta o'zgaruvchan maydonda saqlanardi — shu sabab nashr qilingandan keyin ham eski xabar ko'rinib qolgan edi (bug — tuzatilgan).

**Boshqa jurnal tizimlari (OJS, Editage, Charlesworth, Editorial Manager va h.k.) tadqiqotiga asoslanib** qabul qilingan yechim:

1. **Minor / Major revision** — admin/muharrir "muallifga qaytarish"da tanlaydi:
   - **Kichik tuzatish**: mualif qayta yuklagach to'g'ridan-to'g'ri o'sha admin/muharrirning o'ziga qaytadi — tahrirchilar qayta biriktirilmaydi, taqriz 0dan boshlanmaydi.
   - **Katta tuzatish**: to'liq qayta taqriz sikli (avvalgidek).
2. **Tuzatishlar tarixi** (`submission_revision_rounds` jadvali) — har bir qaytarish alohida yozuv sifatida saqlanadi (kim ochdi, sababi, muharrir fayli, hal qilingan vaqti). Mualif dashboardida "Tuzatishlar tarixi" ro'yxati ko'rinadi — bitta o'zgaruvchan maydon emas, shuning uchun hech qachon eskirib, boshqa bosqichga aralashib qolmaydi.

Migratsiya DB'ga qo'llandi, konteynerlar restart qilindi, 67 test o'tdi.

**Keyinroq qo'shilishi mumkin bo'lgan qo'shimcha (hali qilinmagan, alohida so'ralganda)**:
- B3 — `revision_required` uchun ham muddat + avtomatik eslatma (mavjud `editor_assignments`dagi `acceptance_deadline_at`/`completion_deadline_at` naqshiga o'xshab).

---

Tadqiqot manbalari:
- [Editorial decision-making: possible outcomes — Editage](https://www.editage.com/insights/editorial-decision-making-what-are-the-possible-outcomes-for-a-manuscript)
- [What does 'revisions required' really mean — Charlesworth](https://www.cwauthors.com/article/What-does-a-revisions-required-editorial-decision-really-mean)
- [Conditional acceptance — Proof-Reading-Service](https://www.proof-reading-service.com/blogs/academic-publishing/the-pleasures-and-pains-of-conditional-acceptance)
- [Manuscripts processing and peer review system spec](https://www.editorialsystem.com/docs/EditorialSystem_Specification_EN.pdf)
- [Reminders to keep peer review moving — Scholastica](https://blog.scholasticahq.com/post/reminders-to-keep-peer-review-moving/)
- [OJS Editorial Workflow Overview](https://openjournalsystems.com/ojs-3-user-guide/editorial-workflow-overview/)
