-- Fix editorial_policy page: remove <div class="editorial-policy-content"> wrapper
-- that broke CSS (.info-page-content > section selector requires direct children).
-- Also syncs all 3 language versions with update_pages.py PAGES_DATA.

UPDATE pages
SET
    title = 'Editorial Policy',
    title_uz = 'Tahririyat siyosati',
    title_ru = 'Редакционная политика',
    content = $EDPOL_EN$
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Editorial Policy Overview</h4>
          <p class="mb-4">The following rules apply to the electronic scientific-methodological journal <strong>Philology Matters</strong>. Please read this policy in full before submission to ensure full compliance with journal requirements.</p>
          <p class="mb-0">The journal follows internationally recognized publication ethics principles, including relevant COPE recommendations.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Affiliation</h4>
          <p class="mb-3">All relevant affiliations must be provided to indicate where the research was approved, supported, and/or conducted.</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Author full names in 3 languages (Uzbek, Russian, English).</li>
            <li>Academic degree, title, and position in 3 languages.</li>
            <li>Region/country of residence in 3 languages.</li>
            <li>Email addresses and phone numbers.</li>
            <li>ORCID iD.</li>
            <li>If available: Google Scholar and Scopus profile links.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Appeals and Complaints</h4>
          <p class="mb-4">The journal follows COPE guidance for appeals against editorial decisions and complaints about editorial process management. Substantive appeals are considered when supported by clear arguments, evidence, or new information.</p>
          <p class="mb-0">For process-related complaints, contact the editorial office and select the relevant category. Authors are encouraged to consult the journal's full appeals and complaints guidance (Appendix 9 and Appendix 10).</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Authorship</h4>
          <p class="mb-3">Listing author names is a core mechanism for recognizing scholarly contribution and ensuring responsibility for research integrity.</p>
          <p class="mb-3">All listed authors must meet all criteria below:</p>
          <ol class="list-decimal list-inside space-y-2">
            <li>Substantial contribution to concept, design, execution, data collection, analysis, interpretation, or these components collectively.</li>
            <li>Drafting the manuscript or critically revising it for important intellectual content.</li>
            <li>Joint decision on journal submission.</li>
            <li>Review and approval of all manuscript versions, including revised and final accepted versions and any substantial corrections.</li>
          </ol>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Determining Authorship</h4>
          <p class="mb-4">Decisions on who is listed as an author and in what order are the shared responsibility of all contributors.</p>
          <p class="mb-0">Editors do not arbitrate unresolved authorship disputes. If disagreement persists, the matter is referred to the relevant institution(s). Authors should consult the journal guidance on authorship, authorship changes, acknowledgements, language/translation support, analytical assistance, and author-name change policy.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Citation Policy</h4>
          <p class="mb-4">Claims must be supported by relevant, timely, peer-reviewed literature where appropriate. Excessive self-citation and coordinated citation arrangements intended to manipulate citation records are prohibited.</p>
          <p class="mb-4">Authors of non-research articles (such as reviews or opinions) must ensure fair, balanced, and current coverage of the field and avoid unfair concentration on specific groups, institutions, or journals.</p>
          <p class="mb-0">If you are uncertain about citation practice, contact the journal and review the full citation guidance, including references that should be included in the bibliography.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Competing Interests</h4>
          <p class="mb-4">Authors and co-authors must disclose any competing interests relevant to the manuscript or that may reasonably be perceived as relevant.</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Competing interests may be financial or non-financial.</li>
            <li>Possible sources include employment, sponsorship, legal, commercial, academic, or personal/professional relationships.</li>
            <li>Potentially perceived competing interests should also be disclosed for transparency.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Corrections, Expressions of Concern, and Retractions</h4>
          <p class="mb-4">Post-publication changes are made only after editorial and ethics review in accordance with COPE principles.</p>
          <p class="mb-0">Where required, changes are linked to a formal notice (correction, expression of concern, retraction, or in rare cases removal) to preserve the integrity and transparency of the scholarly record.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Data Availability and Preservation</h4>
          <p class="mb-0">The journal applies a data-sharing policy for manuscript-associated datasets and expects authors to provide data availability information and preserve relevant research data in suitable repositories when applicable.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Data Sharing Policy and Repositories</h4>
          <p class="mb-4">If your study includes datasets, follow the journal's data-sharing guidance and repository-selection instructions.</p>
          <p class="mb-0">A data repository is a virtual platform for storing and providing access to research datasets. Authors should choose a repository appropriate to discipline, access conditions, and preservation requirements.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Code, Software, and Algorithms</h4>
          <p class="mb-0">To enable complete evaluation, authors must provide custom code, software tools, and mathematical algorithms used to generate reported results when requested by editors and/or reviewers.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Territorial Designations</h4>
          <p class="mb-0">The journal remains neutral regarding jurisdictional claims and territorial designations in published content, including maps and institutional affiliations, while respecting author usage and relevant third-party policy context.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Editor Code of Conduct</h4>
          <p class="mb-4">Editors safeguard publication quality, peer-review integrity, and fair process for authors and reviewers.</p>
          <p class="mb-0">The journal's editorial conduct code defines minimum standards to ensure consistent publication of high-quality and reliable scholarship.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Funding Disclosure</h4>
          <p class="mb-4">Authors must disclose all funding sources that supported the work reported in the manuscript.</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Internal institutional funding, grants, or employer support.</li>
            <li>External funding (charities, foundations, non-profit or private organizations, companies, associations, government bodies, etc.).</li>
            <li>Support for research implementation, analysis, language editing, translation, scientific writing, or travel related to the project.</li>
          </ul>
          <p class="mb-4">Funding statements should include the full funder name, grant number(s), and ideally the funded person/group. If funders had an active role in research conduct or analysis, this must also be disclosed as a competing interest.</p>
          <p class="mb-0">If no funding was received, authors should explicitly state this. Non-disclosure or material inaccuracy may trigger correction or retraction actions.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Author Ethics</h4>
          <p class="mb-4">The journal does not tolerate pressure, intimidation, or coercive behavior directed at authors, editors, reviewers, staff, or service providers.</p>
          <p class="mb-0">Editorial teams operate under mutual respect and coordinate with ethics and legal specialists where needed. Researchers facing online harassment are encouraged to follow the journal's guidance on handling social-media pressure.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Figures and Illustrations</h4>
          <p class="mb-0">Figures and visual materials should be included only when they are relevant and add scientific value. Decorative or non-informative visual content should be avoided.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Use of Third-Party Materials</h4>
          <p class="mb-4">Authors are responsible for obtaining permissions for third-party copyright-protected content (text, tables, illustrations, photos, audio, video, screenshots, music notation, and supplementary files).</p>
          <p class="mb-0">Limited quotation for criticism/review may be permitted in some cases. For all other protected content, written permission must be obtained before submission.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Permissions for Identifiable or Protected Content</h4>
          <p class="mb-4">Content that may identify research participants or protected subjects (including images, audio/video, 3D models, and similar materials) may be published only with informed consent from participants or lawful representatives.</p>
          <p class="mb-0">Where additional community or archive permissions are required, authors must secure and retain relevant documents before submission.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Misconduct</h4>
          <p class="mb-3">The journal treats all forms of misconduct seriously and applies COPE-aligned procedures to protect research integrity.</p>
          <p class="mb-3">Examples include, but are not limited to:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Misrepresentation of affiliation.</li>
            <li>Copyright infringement or use of third-party materials without permission.</li>
            <li>Citation manipulation.</li>
            <li>Duplicate submission/publication.</li>
            <li>Image or data fabrication/manipulation.</li>
            <li>Peer-review manipulation.</li>
            <li>Plagiarism and self-plagiarism/text recycling.</li>
            <li>Undisclosed competing interests.</li>
            <li>Unethical research conduct.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Double-Blind Peer Review</h4>
          <p class="mb-4">Research manuscripts are assessed through rigorous double-blind peer review under journal and COPE reviewer guidance.</p>
          <p class="mb-4">Typically, each manuscript is reviewed by at least two independent reviewers. Reviewer reports and recommendations inform editorial decisions, while final responsibility rests with the editor.</p>
          <p class="mb-0">The journal does not permit authors to nominate their own reviewers.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Confidentiality in Peer Review</h4>
          <p class="mb-4">Confidentiality and integrity must be preserved throughout review and editorial decision-making in compliance with applicable data protection standards, including GDPR principles where relevant.</p>
          <p class="mb-0">Reviewers must disclose competing interests before submitting reports. During ethics investigations, manuscript-related information remains confidential and is shared only where necessary with authorized parties.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Plagiarism</h4>
          <p class="mb-4">The journal takes plagiarism seriously in all formats (digital or print), including text, ideas, figures, and other materials used directly or indirectly without proper acknowledgment.</p>
          <p class="mb-0">Authors must always cite original sources and follow journal plagiarism guidance.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Preprints and Early Reports</h4>
          <p class="mb-4">The journal supports responsible sharing of early manuscript versions. Posting an Author Original Manuscript to a non-commercial preprint server before submission is not considered duplicate publication.</p>
          <p class="mb-0">After publication, authors may share permitted manuscript versions according to journal dissemination guidance.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Promoting Published Articles</h4>
          <p class="mb-0">Authors are encouraged to promote published work responsibly through scholarly channels, in line with journal policy on version sharing and citation accuracy.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Research Ethics and Consent</h4>
          <p class="mb-0">All published research must be conducted in accordance with relevant international and local ethical standards, including appropriate informed-consent and approval procedures where applicable.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Reporting Standards</h4>
          <p class="mb-0">Manuscripts should provide sufficiently detailed rationale, protocol, methodology, and analysis to support validation and reproducibility. Authors are encouraged to follow discipline-appropriate reporting guidelines before submission.</p>
        </section>
$EDPOL_EN$,
    content_uz = $EDPOL_UZ$
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahririyat siyosati haqida</h4>
          <p class="mb-4">Quyidagi qoidalar <strong>"Filologiya masalalari"</strong> elektron ilmiy-metodik jurnaliga tegishli. Iltimos, maqolangizni yuborishdan oldin ushbu siyosatni to'liq o'qib chiqing.</p>
          <p class="mb-0">Jurnal nashr etikasi bo'yicha xalqaro yondashuvlarga, jumladan COPE tavsiyalariga amal qiladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Mansublik</h4>
          <p class="mb-3">Tadqiqot qayerda tasdiqlangan, qo'llab-quvvatlangan yoki o'tkazilganini ko'rsatish uchun barcha tegishli mansublik ma'lumotlari keltirilishi shart.</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Mualliflarning F.I.Sh. - 3 tilda (o'zbek, rus, ingliz).</li>
            <li>Ilmiy daraja, unvon va lavozim - 3 tilda.</li>
            <li>Mualliflarning istiqomat hududi nomi - 3 tilda.</li>
            <li>Elektron pochta manzillari va telefon raqamlari.</li>
            <li>ORCID iD raqami.</li>
            <li>Mavjud bo'lsa: Google Scholar va Scopus havolalari.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Apellyasiya va shikoyatlar</h4>
          <p class="mb-4">Jurnal muharrirlar qarorlari va tahririy boshqaruv bo'yicha murojaatlarda COPE yo'riqnomalariga amal qiladi. Murojaatlar mazmunli dalillar va yangi asoslar bilan taqdim etilishi kerak.</p>
          <p class="mb-0">Jarayon bo'yicha shikoyatlar uchun tahririyatga murojaat qiling. Mualliflar 9-ILOVA va 10-ILOVAdagi to'liq qo'llanmalarni ko'rib chiqishlari tavsiya etiladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Mualliflik</h4>
          <p class="mb-3">Mualliflar ro'yxati ilmiy hissa va mazmun yaxlitligi uchun mas'uliyatni shaffof aks ettirishi kerak.</p>
          <p class="mb-3">Maqolada ko'rsatilgan har bir muallif quyidagi barcha mezonlarga javob berishi lozim:</p>
          <ol class="list-decimal list-inside space-y-2">
            <li>Tadqiqot konsepsiyasi, dizayni, bajarilishi, ma'lumot yig'ish, tahlil va sharhlash bosqichlarida sezilarli hissa qo'shgan bo'lishi.</li>
            <li>Maqolani yozgan, muhim darajada tahrir qilgan yoki tanqidiy ko'rib chiqqan bo'lishi.</li>
            <li>Maqolani qaysi jurnalga yuborish bo'yicha birgalikda qaror qilgan bo'lishi.</li>
            <li>Taqdim etishdan oldingi, qayta ko'rib chiqilgan va qabul qilingan yakuniy versiyalarni, shuningdek muhim tuzatishlarni tasdiqlagan bo'lishi.</li>
          </ol>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Mualliflikni aniqlash</h4>
          <p class="mb-4">Mualliflar ro'yxati va tartibini belgilash tadqiqotda ishtirok etgan shaxslarning umumiy mas'uliyatidir.</p>
          <p class="mb-0">Muharrir mualliflik nizolarida hakamlik qilmaydi. Hal etilmagan nizolar tegishli muassasa(lar)ga yuboriladi. Mualliflar mualliflik, mualliflik o'zgarishi, minnatdorchilik, tarjimon/ilmiy yozuvchi yordami va muallif nomini o'zgartirish siyosati bo'yicha qo'llanmani o'qishlari zarur.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Iqtibos siyosati</h4>
          <p class="mb-4">Maqoladagi da'volar dolzarb, o'z vaqtida va o'zaro ko'rib chiqilgan manbalar bilan asoslanishi kerak. Haddan tashqari o'z-o'zidan iqtibos keltirish va iqtibos manipulyasiyasi qat'iyan man etiladi.</p>
          <p class="mb-4">Sharh yoki fikr-mulohaza turidagi maqolalarda adabiyotlar tahlili adolatli, muvozanatli va mavzuning hozirgi holatini aks ettiruvchi bo'lishi kerak.</p>
          <p class="mb-0">Iqtibos berish bo'yicha noaniqlik bo'lsa, jurnalga murojaat qiling va to'liq iqtibos qo'llanmasidan foydalaning.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Raqobatdosh manfaatlar</h4>
          <p class="mb-4">Mualliflar va hammualliflar maqolaga aloqador bo'lishi mumkin bo'lgan barcha raqobatdosh manfaatlarni alohida e'lon qilishlari kerak.</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Manfaatlar moliyaviy va nomoliyaviy bo'lishi mumkin.</li>
            <li>Moliyaviy, tijorat, huquqiy, professional yoki shaxsiy bog'liqliklar natijalarga ta'sir qilishi mumkin.</li>
            <li>Boshqalar tomonidan manfaatlar to'qnashuvi sifatida qabul qilinishi mumkin bo'lgan holatlar ham oshkor etilishi kerak.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tuzatishlar, tashvish izhorlari va raddiyalar</h4>
          <p class="mb-4">Nashrdan keyingi o'zgartirishlar faqat muharririy va axloqiy tekshiruvdan so'ng, COPE tamoyillari asosida amalga oshiriladi.</p>
          <p class="mb-0">Zarur hollarda tuzatish, tashvish ifodasi, rad etish (retraction) yoki kamdan-kam holatda olib tashlash haqidagi rasmiy bildirishnoma beriladi va u asl maqola bilan doimiy bog'lanadi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ma'lumotlar mavjudligi va saqlash</h4>
          <p class="mb-0">Jurnal ma'lumotlar almashish siyosatini qo'llaydi va maqola bilan bog'liq ma'lumotlar to'plamining mavjudligi hamda saqlanishi bo'yicha aniq bayonot berilishini kutadi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ma'lumotlar almashish siyosati va omborlar</h4>
          <p class="mb-4">Agar tadqiqotingizga ma'lumotlar to'plami hamroh bo'lsa, uni jurnal siyosatiga muvofiq ulashish tartiblariga amal qiling.</p>
          <p class="mb-0">Ma'lumotlar ombori - tadqiqot ma'lumotlarini saqlash va ulashish uchun virtual maydon. Mualliflar mos omborni yo'nalish, ochiqlik va saqlash talablariga ko'ra tanlashlari kerak.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kompyuter kodlari, dasturiy vositalar va algoritmlar</h4>
          <p class="mb-0">Natija va xulosalarni olishda qo'llangan maxsus kodlar, dasturiy vositalar va matematik algoritmlar muharrirlar yoki taqrizchilar so'roviga binoan taqdim etilishi shart.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Hudud belgilari</h4>
          <p class="mb-0">Jurnal xaritalar, institusional mansubliklar va hududiy belgilashlar bo'yicha yurisdiksion da'volarga nisbatan betaraf pozitsiyani saqlaydi va muallif qo'llanishlarini hurmat qiladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Muharrirning axloq kodeksi</h4>
          <p class="mb-4">Muharrirlar nashr sifati, yopiq taqriz jarayoni yaxlitligi hamda mualliflar va taqrizchilar bilan adolatli ishlash uchun javobgardir.</p>
          <p class="mb-0">Jurnal tahririy xulq-atvor kodeksi ishonchli va sifatli ilmiy kontentni ta'minlash uchun minimal standartlarni belgilaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Moliyalashtirish</h4>
          <p class="mb-4">Mualliflar maqolada keltirilgan ishni qo'llab-quvvatlagan barcha moliyalashtirish manbalarini oshkor etishlari shart.</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Ichki mablag'lar: muassasa, ish beruvchi yoki bog'liq tashkilot grantlari va yordami.</li>
            <li>Tashqi mablag'lar: xayriya/notijorat tashkilotlari, jamg'armalar, kompaniyalar, tahlil markazlari, davlat idoralari va boshqalar.</li>
            <li>Tadqiqot o'tkazish, tahlil, tarjima, ilmiy yozuv, til tahriri va safar xarajatlarini qoplashga yo'naltirilgan mablag'lar.</li>
          </ul>
          <p class="mb-4">Moliyaviy bayonotda moliyalashtiruvchi to'liq nomi, grant raqami va imkon qadar grant oluvchi shaxs/guruh ko'rsatilishi kerak. Homiyning tadqiqotdagi faol roli raqobatdosh manfaatlar deklaratsiyasida ham alohida qayd etiladi.</p>
          <p class="mb-0">Agar mablag' olinmagan bo'lsa, buni aniq yozish tavsiya etiladi. Moliyalashtirishni yashirish yoki noto'g'ri ko'rsatish tuzatish/rad etish choralariga olib kelishi mumkin.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Muallif etikasi</h4>
          <p class="mb-4">Jurnal mualliflar, muharrirlar, taqrizchilar, xodimlar yoki hamkorlarga nisbatan har qanday bosim va tazyiqni qabul qilmaydi.</p>
          <p class="mb-0">Tahririyat o'zaro hurmat muhitida ishlaydi va zarur holatlarda axloq hamda huquq bo'yicha mutaxassislar bilan hamkorlikda masalalarni ko'rib chiqadi. Onlayn bosimlarga duch kelgan tadqiqotchilar jurnal tavsiyalaridan foydalanishlari mumkin.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tasvir va chizmalar</h4>
          <p class="mb-0">Tasvirlar va chizmalar faqat tadqiqot uchun ilmiy qiymat qo'shganda berilishi kerak. Dekorativ yoki mavzuga aloqasiz materiallardan foydalanish tavsiya etilmaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Uchinchi tomon materiallaridan foydalanish</h4>
          <p class="mb-4">Mualliflar uchinchi shaxsga tegishli mualliflik huquqi bilan himoyalangan materiallar (matn, jadval, illyustratsiya, foto, audio, video, skrinshot, nota va ilovalar) uchun zarur ruxsatlarni oldindan olishlari shart.</p>
          <p class="mb-0">Tanqidiy tahlil uchun qisqa iqtiboslarga ayrim holatlarda rasmiy ruxsatsiz cheklangan foydalanish mumkin, ammo boshqa holatlarda yozma ruxsat majburiy.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Identifikatsiya qilinadigan yoki himoyalangan kontent uchun ruxsat</h4>
          <p class="mb-4">Shaxsni aniqlashga olib kelishi mumkin bo'lgan kontent (foto, video, audio, 3D model va boshqalar) faqat ishtirokchining yoki qonuniy vakilining xabardor roziligi bilan nashr etiladi.</p>
          <p class="mb-0">Agar qo'shimcha ruxsat talab etiladigan jamoa yoki himoyalangan manbadan foydalanilgan bo'lsa, mualliflar qo'lyozma topshirishdan oldin barcha hujjatlarni rasmiylashtirishi kerak.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Qonunbuzarlik</h4>
          <p class="mb-3">Jurnal qonunbuzarlikning barcha shakllarini jiddiy qabul qiladi va ilmiy yozuvlar yaxlitligini himoya qilish uchun COPE ko'rsatmalariga muvofiq choralar ko'radi.</p>
          <p class="mb-3">Misollar (lekin ular bilan cheklanmaydi):</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Mansublikni noto'g'ri ko'rsatish.</li>
            <li>Mualliflik huquqini buzish yoki ruxsatsiz uchinchi tomon materiallaridan foydalanish.</li>
            <li>Iqtibos manipulyasiyasi.</li>
            <li>Takroriy topshirish yoki takroriy nashr.</li>
            <li>Tasvir yoki ma'lumotlarni soxtalashtirish/manipulyasiya qilish.</li>
            <li>Yopiq taqriz jarayonini manipulyasiya qilish.</li>
            <li>Plagiat va o'z-o'zidan plagiat (matnni qayta ishlatish).</li>
            <li>Ochilmagan raqobatdosh manfaatlar.</li>
            <li>Axloqiy bo'lmagan tadqiqot amaliyotlari.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ikki tomonlama yopiq taqriz jarayoni</h4>
          <p class="mb-4">Maqolalar COPE talablariga mos ikki tomonlama yopiq taqriz asosida ekspertizadan o'tkaziladi. Odatda har bir maqola kamida ikki mustaqil taqrizchi tomonidan baholanadi.</p>
          <p class="mb-4">Taqriz xulosalari muharrir qaroriga asos bo'ladi, biroq yakuniy qaror uchun mas'uliyat muharrir zimmasida qoladi.</p>
          <p class="mb-0">Jurnal mualliflarga taqrizchilarni o'zlari tavsiya qilish huquqini bermaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yopiq taqriz jarayonining maxfiyligi</h4>
          <p class="mb-4">Ko'rib chiqish va tahririy qarorlar jarayonida maxfiylik hamda yaxlitlik ma'lumotlarni himoya qilish talablariga muvofiq saqlanadi (jumladan, tegishli GDPR tamoyillari).</p>
          <p class="mb-0">Taqrizchilar hisobot topshirishdan oldin raqobatdosh manfaatlarini oshkor etishlari shart. Axloqiy tekshiruvlarda ma'lumotlar faqat vakolatli tomonlar bilan zarur hajmda almashiladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Plagiat</h4>
          <p class="mb-4">Jurnal plagiatga nisbatan qat'iy yondashadi. Bu elektron yoki bosma formatdagi matn, g'oya, tasvir va boshqa materiallardan manba ko'rsatmasdan to'g'ridan-to'g'ri yoki bilvosita foydalanishni o'z ichiga oladi.</p>
          <p class="mb-0">Har qanday holatda asl manba to'g'ri ko'rsatilishi shart.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Preprintlar va dastlabki hisobotlar</h4>
          <p class="mb-4">Jurnal mualliflarning dastlabki versiyalarni mas'uliyatli almashishini qo'llab-quvvatlaydi. Muallifning asl qo'lyozmasini notijorat preprint serveriga joylash takroriy nashr sifatida baholanmaydi.</p>
          <p class="mb-0">Maqola chop etilgach, ruxsat etilgan versiyalarni jurnal qoidalariga muvofiq ulashish mumkin.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Chop etilgan maqolani targ'ib qilish</h4>
          <p class="mb-0">Mualliflar o'z maqolalarini ilmiy hamjamiyatda mas'uliyatli ravishda targ'ib qilishlari mumkin; bunda versiya almashish va to'g'ri iqtibos talablari saqlanishi kerak.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tadqiqot etikasi va rozilik</h4>
          <p class="mb-0">Jurnalda chop etiladigan tadqiqotlar xalqaro va mahalliy etik me'yorlarga muvofiq o'tkazilgan bo'lishi shart, zarur hollarda etik ruxsat va xabardor rozilik hujjatlari taqdim etiladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Hisobot standartlari</h4>
          <p class="mb-0">Tadqiqotlar tasdiqlanishi va takrorlanishini ta'minlaydigan darajada aniq bayon qilinishi kerak. Mualliflarga tadqiqot asoslari, protokol, metodologiya va tahlilni to'liq yoritish hamda mavzuga mos hisobot berish yo'riqnomalaridan foydalanish tavsiya etiladi.</p>
        </section>
$EDPOL_UZ$,
    content_ru = $EDPOL_RU$
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Обзор редакционной политики</h4>
          <p class="mb-4">Ниже приведены правила электронного научно-методического журнала <strong>«Вопросы филологии»</strong>. Перед отправкой статьи внимательно ознакомьтесь с полной редакционной политикой.</p>
          <p class="mb-0">Журнал придерживается международных принципов публикационной этики, включая рекомендации COPE.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Аффилиация</h4>
          <p class="mb-3">Для указания места, где исследование было одобрено, поддержано и/или выполнено, необходимо предоставить все релевантные сведения:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Ф.И.О. авторов на 3 языках (узбекский, русский, английский).</li>
            <li>Ученая степень, звание и должность на 3 языках.</li>
            <li>Регион/страна проживания на 3 языках.</li>
            <li>Адреса электронной почты и телефоны.</li>
            <li>ORCID iD.</li>
            <li>При наличии: ссылки на Google Scholar и Scopus.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Апелляции и жалобы</h4>
          <p class="mb-4">Журнал следует рекомендациям COPE при рассмотрении апелляций на решения редакторов и жалоб на редакционное управление процессом рецензирования. Апелляции рассматриваются при наличии аргументов, доказательств или новой информации.</p>
          <p class="mb-0">По вопросам редакционного процесса обращайтесь в редакцию. Рекомендуется ознакомиться с полными руководствами (Приложение 9 и Приложение 10).</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Авторство</h4>
          <p class="mb-3">Указание авторов является ключевым механизмом признания вклада и обеспечения ответственности за целостность научного содержания.</p>
          <p class="mb-3">Каждый автор должен соответствовать всем критериям:</p>
          <ol class="list-decimal list-inside space-y-2">
            <li>Существенный вклад в концепцию, дизайн, выполнение исследования, сбор, анализ и интерпретацию данных.</li>
            <li>Подготовка текста статьи или ее существенная критическая переработка.</li>
            <li>Совместное решение о подаче рукописи в журнал.</li>
            <li>Одобрение всех версий рукописи, включая доработанные и финальную принятую версию.</li>
          </ol>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Определение авторства</h4>
          <p class="mb-4">Решение о составе и порядке авторов является общей ответственностью всех участников исследования.</p>
          <p class="mb-0">Редактор не выступает арбитром в неурегулированных спорах об авторстве. Такие вопросы передаются в соответствующие организации. Авторам следует изучить руководство по авторству, изменениям авторства, благодарностям, языковой/переводческой поддержке и политике изменения имени автора.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Цитирование</h4>
          <p class="mb-4">Все утверждения должны подкрепляться релевантной, актуальной и рецензируемой литературой. Чрезмерное самоцитирование и согласованные практики цитирования, направленные на манипуляцию, запрещены.</p>
          <p class="mb-4">Для обзорных и дискуссионных работ требуется объективный и сбалансированный анализ текущего состояния исследований без предвзятости к отдельным группам, организациям или журналам.</p>
          <p class="mb-0">При сомнениях в оформлении ссылок обращайтесь в редакцию и используйте полное руководство по цитированию.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Конкурирующие интересы</h4>
          <p class="mb-4">Авторы и соавторы обязаны раскрывать все конкурирующие интересы, связанные с рукописью или потенциально воспринимаемые как связанные.</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Интересы могут быть финансовыми и нефинансовыми.</li>
            <li>К ним относятся коммерческие, юридические, профессиональные и личные связи.</li>
            <li>Даже потенциально воспринимаемые конфликты должны быть раскрыты ради прозрачности.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Исправления, выражения обеспокоенности и отзыв</h4>
          <p class="mb-4">Любые постпубликационные изменения вносятся после редакционной и этической проверки в соответствии с принципами COPE.</p>
          <p class="mb-0">При необходимости публикуется официальное уведомление (исправление, выражение обеспокоенности, отзыв статьи или, в редких случаях, удаление), связанное с исходной публикацией.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Доступность и хранение данных</h4>
          <p class="mb-0">Журнал применяет политику обмена данными и ожидает от авторов заявление о доступности данных, связанных со статьей, а также их надлежащее хранение.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Политика обмена данными и репозитории</h4>
          <p class="mb-4">Если работа сопровождается набором данных, авторы должны соблюдать требования журнала по обмену данными и выбору репозитория.</p>
          <p class="mb-0">Репозиторий данных - это цифровое пространство для хранения и распространения исследовательских данных. Выбор репозитория должен соответствовать тематике исследования и требованиям к доступу/сохранности.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Код, программные средства и алгоритмы</h4>
          <p class="mb-0">По запросу редактора и/или рецензентов авторы обязаны предоставить специализированный код, программные инструменты и алгоритмы, использованные для получения результатов и выводов.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Территориальные обозначения</h4>
          <p class="mb-0">Журнал сохраняет нейтралитет в отношении территориальных и юрисдикционных заявлений в опубликованном контенте, включая карты и институциональные аффилиации.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Кодекс редакторской этики</h4>
          <p class="mb-4">Редакторы отвечают за качество публикаций, целостность двойного слепого рецензирования и поддержку авторов и рецензентов.</p>
          <p class="mb-0">Кодекс редакционного поведения журнала определяет минимальные стандарты для обеспечения надежного и качественного научного контента.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Финансирование</h4>
          <p class="mb-4">Авторы обязаны раскрывать все источники финансирования, связанные с исследованием, представленным в статье.</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Внутренние источники: поддержка организации, работодателя, гранты и иные формы финансирования.</li>
            <li>Внешние источники: фонды, некоммерческие/коммерческие организации, государственные структуры и т.д.</li>
            <li>Финансирование проведения исследования, анализа, языкового редактирования, перевода, научного письма и поездок.</li>
          </ul>
          <p class="mb-4">Финансовое заявление должно содержать полное наименование финансирующей организации, номер гранта и, по возможности, получателя гранта. Активная роль спонсора в исследовании дополнительно отражается в декларации конкурирующих интересов.</p>
          <p class="mb-0">Если финансирование отсутствовало, это следует явно указать. Сокрытие финансирования или существенные неточности могут привести к исправлению или отзыву статьи.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Этика автора</h4>
          <p class="mb-4">Журнал не допускает давление, запугивание или иные формы принуждения в отношении авторов, редакторов, рецензентов, сотрудников или поставщиков услуг.</p>
          <p class="mb-0">Редакция работает в атмосфере взаимного уважения и при необходимости взаимодействует со специалистами по этике и праву. Исследователям, столкнувшимся с онлайн-давлением, рекомендуется пользоваться соответствующими рекомендациями журнала.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Изображения и иллюстрации</h4>
          <p class="mb-0">Иллюстративные материалы следует использовать только при наличии научной ценности и прямой связи с результатами исследования. Декоративный или нерелевантный визуальный контент не рекомендуется.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Использование материалов третьих лиц</h4>
          <p class="mb-4">Авторы несут ответственность за получение разрешений на использование защищенных авторским правом материалов третьих лиц (тексты, таблицы, иллюстрации, фото, аудио, видео, скриншоты, ноты и приложения).</p>
          <p class="mb-0">Ограниченное цитирование в целях критики/обзора может быть допустимо в отдельных случаях, но для иного использования требуется письменное разрешение правообладателя до подачи рукописи.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Разрешение на публикацию идентифицируемого или защищенного контента</h4>
          <p class="mb-4">Контент, позволяющий идентифицировать участников исследования (фото, видео, аудио, 3D-модели и т.д.), публикуется только при наличии информированного согласия участников или их законных представителей.</p>
          <p class="mb-0">Если требуются дополнительные разрешения от сообществ, архивов или иных правообладателей, авторы должны оформить их до подачи рукописи.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Нарушения и недобросовестная практика</h4>
          <p class="mb-3">Журнал серьезно относится ко всем видам нарушений и применяет процедуры, согласованные с COPE, для защиты целостности научной записи.</p>
          <p class="mb-3">Примеры (не ограничиваясь):</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Неверное указание аффилиации.</li>
            <li>Нарушение авторских прав и использование материалов без разрешения.</li>
            <li>Манипуляции цитированием.</li>
            <li>Дублирующая подача/публикация.</li>
            <li>Фальсификация или манипуляция изображениями и данными.</li>
            <li>Манипуляция процессом рецензирования.</li>
            <li>Плагиат и самоплагиат (text recycling).</li>
            <li>Нераскрытые конкурирующие интересы.</li>
            <li>Неэтичное проведение исследования.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Двойное слепое рецензирование</h4>
          <p class="mb-4">Рукописи проходят строгую экспертизу в формате двойного слепого рецензирования в соответствии с требованиями журнала и рекомендациями COPE.</p>
          <p class="mb-4">Обычно статья направляется как минимум двум независимым рецензентам. Редактор учитывает рецензии, но окончательное решение принимает самостоятельно.</p>
          <p class="mb-0">Журнал не принимает предложения авторов по кандидатам в рецензенты.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Конфиденциальность рецензирования</h4>
          <p class="mb-4">На всех этапах рецензирования и принятия редакционных решений должна соблюдаться конфиденциальность и целостность процесса в соответствии с требованиями защиты данных, включая применимые принципы GDPR.</p>
          <p class="mb-0">Рецензенты обязаны раскрывать потенциальные конкурирующие интересы до подачи отчета. При этических расследованиях информация раскрывается только уполномоченным сторонам в необходимом объеме.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Плагиат</h4>
          <p class="mb-4">Журнал строго относится к плагиату во всех форматах (цифровых и печатных), включая текст, идеи, изображения и иные материалы, используемые без надлежащего указания источника.</p>
          <p class="mb-0">Во всех случаях авторы обязаны корректно ссылаться на первоисточники.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Препринты и предварительные версии</h4>
          <p class="mb-4">Журнал поддерживает ответственное распространение ранних версий научных работ. Размещение авторской версии рукописи на некоммерческом сервере препринтов не считается дублирующей публикацией.</p>
          <p class="mb-0">После публикации статьи авторы могут распространять разрешенные версии в соответствии с правилами журнала.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Продвижение опубликованной статьи</h4>
          <p class="mb-0">Авторам рекомендуется распространять публикации через научные каналы с соблюдением правил версионности и корректного цитирования.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Этика исследования и согласие</h4>
          <p class="mb-0">Все исследования, публикуемые в журнале, должны соответствовать международным и локальным этическим требованиям, включая надлежащее информированное согласие и необходимые одобрения.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Стандарты отчетности</h4>
          <p class="mb-0">Рукописи должны содержать достаточное описание обоснования, протокола, методологии и анализа для проверки и воспроизводимости результатов. Перед подачей рекомендуется использовать профильные руководства по отчетности.</p>
        </section>
$EDPOL_RU$,
    last_update = EXTRACT(EPOCH FROM NOW())::bigint
WHERE alias = 'editorial_policy';
