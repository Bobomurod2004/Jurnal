-- Restore Uzbek and Russian translations for aims_scope page
-- Migration 000003 incorrectly set content_uz/content_ru to English text

UPDATE pages
SET
    content_uz = $UZ$<div class="aims-content">

<p>"<strong>Filologiya Masalalari</strong>" elektron ilmiy-uslubiy jurnali filologiya (10.00.00) va pedagogika (13.00.00) kesishmasida bilim, nazariya va metodologiyani rivojlantirishga yo'naltirilgan, butun dunyoda olib borilayotgan tadqiqotlarni nashr etishni qo'llab-quvvatlaydi. Jurnal birinchi (ona), ikkinchi va xorijiy tillarni o'rganish, o'qitish va egallash bilan bog'liq pedagogik muammolar kontekstida til roli va boshqa filologik masalalarni o'rganadi.</p>

<p>Jurnal quyidagi maqsadlarda tadqiqotlarni nashr etadi: ilmiy jamoatchilikka original tadqiqot natijalarini tarqatish imkoniyatini berish; filologiya va pedagogika fanlarida joriy va yangi yo'nalishlarga e'tibor qaratish; o'zbek va xalqaro filologlar o'rtasida ilmiy almashish va hamkorlikni rivojlantirish; O'zbekiston va xalqaro akademik jamiyat uchun muhim bo'lgan tadqiqot natijalarini va konstruktiv g'oyalarni, jumladan filologik fanlarni o'qitishning innovatsion usullarini taqdim etish; O'zbekistonda, MDH mamlakatlarida va keng xalqaro tadqiqotchilar hamjamiyatida ishlab chiqilgan zamonaviy tendentsiyalar, nazariyalar va ularning amaliy tatbiqlarini o'quvchilarga tanishtirish. Jurnal, shuningdek, til, madaniyat, idrok va muloqot o'rtasidagi o'zaro ta'sirni ochib beradigan filologik va pedagogik masalalarning keng doirasini qamrab oluvchi original interdistsiplinar tadqiqotlarni ham nashr etadi.</p>

<p>"Filologiya Masalalari" jurnali til ta'limining har qanday jihatini o'rganish uchun filologiya va pedagogikaning barcha an'analaridan nazariya va metodologiyalarni birlashtirgan tadqiqotlarni rag'batlantiradi. Filologiya va pedagogika kesishmasida o'rganiladigan sohalar tilshunoslik, adabiyotshunoslik, tarjima nazariyasi, jurnalistika, o'qitish metodikasi, pedagogika va psixologiyani o'z ichiga oladi, lekin bular bilan cheklanib qolmaydi.</p>

<p>"Filologiya Masalalari" original tadqiqotlarga yo'naltirilgan jurnal hisoblanadi. Maqolalar ta'lim sohasida amaliy va siyosiy ahamiyatga ega bo'lishi mumkin bo'lsa-da, ular puxta tadqiqotlarga asoslanishi va tahlil hamda muhokamada kuchli kontseptual poydevorni namoyish etishi lozim. Jurnal filologiya va tegishli fanlar sohasini qamrab oluvchi, sifatli, miqdoriy yoki aralash metodli paradigmalarning printsipial qo'llanilishini aks ettiruvchi intizomiy va interdistsiplinar tadqiqot an'analaridan kelib chiqqan eksperimental tadqiqotlar, sharh maqolalar, amaliy hisobotlar va tadqiqot loyihalarini qabul qiladi. Bularga, masalan, amaliy tadqiqot, etnografik dala ishlari, eksperimental va kvazi-eksperimental tadqiqotlar va boshqa ilmiy izlanish shakllari kiradi. Jurnalga taqdim etilayotgan maqolalar xalqaro kitobxon uchun dolzarb va tushunarli bo'lishi kerak.</p>

<p>Filologiya va pedagogika fanlarining barcha jihatlarini ko'rib chiquvchi maqolalar dunyo mamlakatlarining har qandayiga, jamiyatiga, ta'lim muhitiga yoki tiliga qaratilgan bo'lishi mumkin. Bunga birinchi va ikkinchi tilni o'qitish, immersion ta'lim, kontentga asoslangan til ta'limi, ikki tillilik/ko'p tillilik va ta'lim muhitlari bilan bog'liq tadqiqotlar kiradi. Biroq, til va ta'lim kompetentsiyasi faqatgina zamonaviy xorijiy til ta'limi bilan (masalan, zamonaviy xorijiy tillar yoki xorijiy sifatida ingliz tili) cheklanmaydi.</p>

<h4>Ikki tomonlama ko'r taqriz siyosati</h4>

<p>Ushbu jurnalga taqdim etilgan barcha ilmiy maqolalar dastlabki tahririyat tekshiruvi va ikki tomonlama ko'r taqriz jarayonidan o'tkaziladi.</p>

<p>Qo'lyozmangizni taqdim etish bo'yicha ko'rsatmalar uchun <a href="/page/submission_guidelines">Mualliflar uchun yo'riqnoma</a>ni o'qing.</p>

</div>$UZ$,
    content_ru = $RU$<div class="aims-content">

<p>Электронный научно-методический журнал <strong>«Filologiya Masalalari»</strong> поддерживает публикацию исследований, проводимых по всему миру и способствующих развитию знаний, теории и методологии на пересечении филологии (10.00.00) и педагогики (13.00.00). Журнал фокусируется на роли языка и других филологических вопросах в контексте педагогических задач, связанных с изучением, преподаванием и освоением первого (родного), второго и иностранных языков в мире.</p>

<p>Журнал публикует исследования, направленные на: предоставление научному сообществу возможности распространять результаты оригинальных исследований; привлечение внимания к актуальным и новым направлениям в филологических и педагогических науках; содействие научному обмену и сотрудничеству между узбекскими и международными филологами; представление результатов исследований и конструктивных идей, актуальных как для Узбекистана, так и для международного академического сообщества, включая инновационные подходы к преподаванию филологических дисциплин; знакомство читателей с современными тенденциями, теориями и их практическим применением, разработанными в Узбекистане, странах СНГ и международном исследовательском сообществе. Журнал также публикует оригинальные междисциплинарные исследования по широкому кругу актуальных филологических и педагогических вопросов, раскрывающих взаимодействие языка, культуры, познания и коммуникации.</p>

<p>«Filologiya Masalalari» приветствует исследования, интегрирующие теории и методологии всех традиций филологии и педагогики для изучения любого аспекта языкового образования. Области, изучаемые на пересечении филологии и педагогики, включают, но не ограничиваются лингвистикой, литературоведением, переводоведением, журналистикой, методикой преподавания, педагогикой и психологией.</p>

<p>«Filologiya Masalalari» — журнал, ориентированный на оригинальные исследования. Хотя статьи могут иметь практическое и политическое значение для образования, они должны основываться на строгих исследованиях и демонстрировать прочную концептуальную базу в анализе и обсуждении. Журнал принимает экспериментальные исследования, обзорные статьи, практические отчёты и исследовательские проекты по различным областям филологии и смежных дисциплин, опирающихся на дисциплинарные и междисциплинарные исследовательские традиции, отражающие принципиальное применение качественных, количественных или смешанных методов. Статьи, представленные в журнал, должны быть актуальными и доступными для международного читателя.</p>

<p>Статьи, рассматривающие все аспекты филологических и педагогических наук, могут быть посвящены любой стране, обществу, образовательному контексту или языку мира. Это включает исследования, связанные с обучением родному и второму языку, иммерсионным образованием, предметно-языковым обучением, двуязычием/многоязычием и образовательными средами. Языковая и образовательная компетентность не ограничивается только современным иностранным языковым образованием.</p>

<h4>Политика двойного слепого рецензирования</h4>

<p>Все научные статьи, представленные в этот журнал, проходят строгую оценку, включающую первоначальный редакционный отбор и последующий процесс двойного слепого рецензирования.</p>

<p>Для получения инструкций по представлению рукописи, пожалуйста, прочитайте <a href="/page/submission_guidelines">Руководство для авторов</a>.</p>

</div>$RU$,
    last_update = EXTRACT(EPOCH FROM NOW())::bigint
WHERE alias = 'aims_scope';
