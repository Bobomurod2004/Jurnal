import argparse
import sys
import os
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector
from config import *

PAGES_DATA = {
    'submission_guidelines': {
        'title': 'Submission Guidelines',
        'title_uz': 'Maqola yuborish bo\'yicha ko\'rsatmalar',
        'title_ru': 'Руководство по подаче статей',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Before You Submit</h4>
          <p class="mb-4">The manuscript should match the journal's scope, be original, and must not be under review elsewhere.</p>
          <p class="mb-0">The list of authors, author contributions, and any conflicts of interest must be stated clearly.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Required Files</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Main manuscript with full author information.</li>
            <li>An anonymized version for review.</li>
            <li>Figures, tables, and any supplementary materials.</li>
            <li>A short cover letter, if needed.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Structure and Formatting</h4>
          <p class="mb-4">A paper usually includes a title, abstract, keywords, introduction, methodology, results, discussion, conclusion, and references.</p>
          <p class="mb-0">The text should be submitted in <strong>doc/docx</strong> format. Tables and figures must be numbered and supplied with captions and sources where applicable.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ethics and Authorship</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Plagiarism and fabricated data are not acceptable.</li>
            <li>Authorship contributions must be presented fairly.</li>
            <li>All sources should be cited fully and accurately.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Review Process</h4>
          <p class="mb-0">Each manuscript first passes a technical screening and is then evaluated by qualified reviewers. Editorial revisions may be requested when necessary.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yuborishdan oldin</h4>
          <p class="mb-4">Maqola jurnalning mavzu yo'nalishiga mos, original bo'lishi va boshqa nashrlarda ko'rib chiqilmayotgan bo'lishi kerak.</p>
          <p class="mb-0">Mualliflar ro'yxati, hissalar va manfaatlar to'qnashuvi haqida ma'lumot aniq ko'rsatiladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kerakli fayllar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Asosiy qo'lyozma (muallif ma'lumotlari bilan).</li>
            <li>Anonimlashtirilgan versiya (ko'rib chiqish uchun).</li>
            <li>Rasm/jadval va qo'shimcha materiallar.</li>
            <li>Yo'llanma xati (ixtiyoriy, qisqa).</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tuzilishi va format</h4>
          <p class="mb-4">Maqola odatda sarlavha, annotatsiya, kalit so'zlar, kirish, metodologiya, natijalar, muhokama, xulosa va adabiyotlar bo'limlaridan iborat bo'ladi.</p>
          <p class="mb-0">Matn <strong>doc/docx</strong> formatida taqdim etiladi. Jadval va rasmlar raqamlanadi, sarlavha va manba bilan beriladi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Etika va mualliflik</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Plagiat va soxta ma'lumotlarga yo'l qo'yilmaydi.</li>
            <li>Mualliflik hissalari adolatli ko'rsatiladi.</li>
            <li>Manbalar to'liq va aniq keltiriladi.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Ko'rib chiqish jarayoni</h4>
          <p class="mb-0">Har bir maqola avval texnik tekshiruvdan o'tadi, so'ngra mutaxassislar tomonidan ilmiy ekspertiza qilinadi. Zaruratga ko'ra tahririy tuzatishlar so'raladi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Перед отправкой</h4>
          <p class="mb-4">Рукопись должна соответствовать тематике журнала, быть оригинальной и не находиться на рассмотрении в другом издании.</p>
          <p class="mb-0">Список авторов, вклад каждого автора и возможные конфликты интересов должны быть указаны ясно и полностью.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Необходимые файлы</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Основная рукопись с полной информацией об авторах.</li>
            <li>Анонимизированная версия для рецензирования.</li>
            <li>Иллюстрации, таблицы и дополнительные материалы.</li>
            <li>Краткое сопроводительное письмо, если требуется.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Структура и формат</h4>
          <p class="mb-4">Статья обычно включает заголовок, аннотацию, ключевые слова, введение, методологию, результаты, обсуждение, выводы и список литературы.</p>
          <p class="mb-0">Текст подается в формате <strong>doc/docx</strong>. Таблицы и рисунки должны быть пронумерованы и сопровождаться заголовками и указанием источника при необходимости.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Этика и авторство</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Плагиат и фальсификация данных недопустимы.</li>
            <li>Вклад авторов должен быть отражен справедливо.</li>
            <li>Все источники необходимо указывать полно и точно.</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Процесс рассмотрения</h4>
          <p class="mb-0">Каждая рукопись сначала проходит техническую проверку, после чего направляется на научное рецензирование. При необходимости редакция может запросить доработку текста.</p>
        </section>
        '''
    },
    'author_instructions': {
        'title': 'Instructions for Authors',
        'title_uz': 'Mualliflar uchun ko\'rsatmalar',
        'title_ru': 'Инструкции для авторов',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Instructions for Authors</h4>
          <p class="mb-4">Thank you for choosing the electronic scientific-methodological journal <strong>Philology Matters</strong> for publishing your manuscript. These instructions are essential to ensure an efficient workflow for double-blinded peer review, editorial processing, and publication.</p>
          <p class="mb-0">Please review this guidance carefully so that your manuscript fully complies with the journal requirements.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Table of Contents</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>About the Journal</li>
            <li>Open Access</li>
            <li>Peer Review and Ethics</li>
            <li>Preparing Your Manuscript</li>
            <li>Article Types</li>
            <li>Format-Free Submission</li>
            <li>Editing Services</li>
            <li>Submission Checklist</li>
            <li>Using Third-Party Materials</li>
            <li>Submitting Your Manuscript</li>
            <li>Publication Fee</li>
            <li>Copyright Options</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">About the Journal</h4>
          <p class="mb-4"><strong>Philology Matters</strong> is an electronic scientific-methodological journal publishing high-quality and original research outputs.</p>
          <p class="mb-4">Articles are accepted in all languages. The journal accepts the following manuscript categories:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Original Research Article</li>
            <li>Review Article</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Open Access</h4>
          <p class="mb-4">Through the journal's Open Select model, authors can publish their work under open access conditions. This policy enables immediate online availability after publication and supports wider visibility, readership growth, and increased scholarly impact.</p>
          <p class="mb-0">To select open access publication, an Article Publishing Charge applies. In many cases, this cost may be covered by your institution or funder.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Peer Review and Ethics</h4>
          <p class="mb-4">The publisher of <strong>Philology Matters</strong> is committed to the integrity of expert evaluation and follows high editorial standards in manuscript assessment.</p>
          <p class="mb-0">After editorial suitability screening, each manuscript undergoes <strong>double-blinded peer review</strong> by two independent anonymous reviewers. Authors are required to follow publication ethics throughout submission, review, and publication stages.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Preparing Your Manuscript</h4>
          <p class="mb-4">The manuscript should follow a clear and consistent structure. Required elements are listed below:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Title in 3 languages: Uzbek, Russian, and English.</li>
            <li>Abstract and keywords in 3 languages: Uzbek, Russian, and English.</li>
            <li>Main text in IMRAD order: <strong>INTRODUCTION</strong>, <strong>METHODS</strong>, <strong>RESULTS</strong>, and <strong>DISCUSSION</strong>.</li>
            <li>Optional sections: acknowledgements, conflict-of-interest statement, recommendations.</li>
            <li>Appendices.</li>
            <li>Tables with titles (on separate pages if needed).</li>
            <li>Figures and, where applicable, a separate list of figure captions.</li>
          </ul>
          <ul class="list-disc list-inside space-y-1">
            <li>Abstract length: 250-300 words in each language, including research purpose, novelty, methods, major findings, and key conclusions.</li>
            <li>Keywords: up to 8-10 terms in each language.</li>
            <li>Main text length (from introduction to conclusion): 4,000-7,000 words (excluding abstract and keywords).</li>
            <li>References: 30-60 entries in Latin script, with English translation where required for non-English manuscripts.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Article Types</h4>
          <div class="space-y-4">
            <div>
              <h5 class="font-semibold mb-2">1. Original Research Article</h5>
              <p class="mb-3">An empirical study conducted by the author, based on independently collected and analyzed data. IMRAD section headings must be written in <strong>FULL CAPITAL LETTERS</strong>.</p>
              <ul class="list-disc list-inside space-y-2">
                <li><strong>INTRODUCTION:</strong> relevance of the topic, statement of the scientific problem, short literature overview, research gap, objectives, tasks, and hypothesis (if applicable).</li>
                <li><strong>METHODS:</strong> research design, object and subject, data-collection tools (survey, interview, observation, text/corpus analysis), sample description (size and parameters), analysis methods (SPSS, R, linguistic/cognitive), reliability and validity.</li>
                <li><strong>RESULTS:</strong> factual findings only, including tables/graphs/diagrams (if available), statistical indicators, and identified patterns.</li>
                <li><strong>DISCUSSION:</strong> interpretation of findings, comparison with prior studies, hypothesis confirmation/refutation, theoretical significance, practical significance, limitations, and future research directions.</li>
                <li><strong>CONCLUSION</strong> (mandatory, outside IMRAD): final conclusions, scholarly novelty, concise synthesis, no citations.</li>
              </ul>
            </div>
            <div>
              <h5 class="font-semibold mb-2">2. Review Article</h5>
              <p class="mb-3">A systematic analysis, comparison, and synthesis of previously published studies in a defined scientific field. New empirical data collection is not required.</p>
              <ul class="list-disc list-inside space-y-2">
                <li><strong>INTRODUCTION:</strong> relevance of the field, justification of review necessity, problem statement, review objective, and clear identification of scientific gap.</li>
                <li><strong>METHODS:</strong> source-selection criteria, time range, databases (Scopus, Web of Science, etc.), search strategy (keywords), inclusion/exclusion criteria, analysis methods (thematic review, meta-analysis where applicable).</li>
                <li><strong>RESULTS:</strong> major approaches in the literature, theoretical schools, contradictions, current trends, and comparative tables.</li>
                <li><strong>DISCUSSION:</strong> synthesized conclusions from literature, evaluation of existing approaches, identification of gaps, problematic aspects, and future research perspectives.</li>
                <li><strong>CONCLUSION</strong> (mandatory, outside IMRAD): final synthesis, theoretical conclusions, recommendations, no citations.</li>
              </ul>
            </div>
          </div>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Format-Free Submission</h4>
          <p class="mb-4">Authors may submit manuscripts in any scientific style or arrangement at the initial stage. Submissions can be provided as one or multiple files, typically in Word format (DOC or DOCX). Tables and figures may be embedded in the text or uploaded as separate files.</p>
          <p class="mb-4">Although strict formatting is not required at first submission, each manuscript must include core elements for initial editorial evaluation: abstract, primary author information (full name, position, academic degree, email, phone number in 3 languages), figures, tables, and appendices.</p>
          <p class="mb-0">References must be prepared in <strong>APA (American Psychological Association)</strong> style. Regardless of initial file format, an editable manuscript version must be provided at the revision stage.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Editing Services</h4>
          <p class="mb-4">The publisher of <strong>Philology Matters</strong> offers editorial support services to help improve your manuscript before submission.</p>
          <p class="mb-0">Available options may include language editing (including English), grammar and spelling correction, and technical formatting support. For service scope and fees, please contact the editorial office.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Submission Checklist</h4>
          <ol class="list-decimal list-inside space-y-3">
            <li><strong>Author details:</strong> ensure all listed authors meet the journal authorship criteria. The cover page must include full name, position, academic degree, email, and phone number for each author. Include ORCID, Google Scholar, and Scopus links when available. Note: author details cannot be changed after publication.</li>
            <li><strong>Figures:</strong> supply high-quality files (1200 dpi for line art, 600 dpi for grayscale, 300 dpi for color) in accepted formats: EPS, PS, JPEG, TIFF, or Word (DOC/DOCX for Word-drawn figures).</li>
            <li><strong>Tables:</strong> tables should provide additional value rather than duplicate text and should be understandable independently. Submit editable table files.</li>
            <li><strong>Equations:</strong> when submitting in Word format, equations must remain editable.</li>
          </ol>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Using Third-Party Materials</h4>
          <p class="mb-4">Authors must obtain necessary permissions to reuse third-party materials in their manuscripts. Limited use of short text excerpts for critical discussion may be permitted without formal permission in some cases.</p>
          <p class="mb-0">If your manuscript contains any material for which you do not hold copyright and that is not covered by fair use or similar provisions, written permission from the copyright holder must be obtained before submission.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Submitting Your Manuscript</h4>
          <p class="mb-4">This journal uses a dedicated submission portal to manage manuscript workflow. The portal allows you to track all your submissions within the <strong>Philology Matters</strong> portfolio in one place.</p>
          <p class="mb-4">After technical pre-screening, manuscripts that meet basic requirements are checked with <strong>antiplagiat.ru</strong> for originality. By submitting your manuscript, you consent to originality checks during peer review and editorial processing.</p>
          <p class="mb-0">After acceptance, we recommend keeping a copy of the accepted manuscript version in your records.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Publication Fee</h4>
          <p class="mb-0">The annual publication fee for one article in <strong>Philology Matters</strong> is <strong>600,000 UZS</strong> for citizens of the Republic of Uzbekistan and <strong>100 USD</strong> for other authors.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Copyright Options</h4>
          <p class="mb-4">Copyright protects your original work and helps prevent unauthorized use of your article. The journal offers several licensing and reuse models, including <strong>Creative Commons</strong> options for open access publication.</p>
          <p class="mb-0">For questions, please contact: <a href="mailto:philologymatters@uzswlu.uz" class="text-fmmain hover:underline">philologymatters@uzswlu.uz</a>.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Mualliflar uchun ko'rsatmalar</h4>
          <p class="mb-4">Maqolangizni nashr qilishda <strong>“Filologiya masalalari”</strong> elektron ilmiy-metodik jurnalini tanlaganingiz uchun tashakkur. Ushbu ko'rsatmalar sizning qo'lyozmangizni ikki karra o'zaro yashirin baholash (double-blinded peer review), tahrirlash va nashr etish jarayonlarini oson ta'minlash borasidagi zarur sharoitlarni yaratish uchun muhim.</p>
          <p class="mb-0">Iltimos, ularni o'qishga vaqt ajrating va iloji boricha diqqat bilan ko'rib chiqing, chunki bu qo'lyozmangizning jurnal talablariga javob berishini kafolatlaydi.</p>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal haqida</h4>
          <p class="mb-4"><strong>“Filologiya masalalari”</strong> yuqori sifatli, original tadqiqotlarni nashr etuvchi elektron ilmiy-metodik jurnal hisoblanadi.</p>
          <p class="mb-4">Jurnalda barcha tillarda maqolalar e'lon qilinadi. Jurnalning asosiy fokusi va ekspertiza siyosati haqida ma'lumot olish uchun jurnalning maqsadlari va qamroviga e'tibor qarating.</p>
          <p class="mb-2">Jurnal quyidagi maqola turlarini qabul qiladi:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Original tadqiqot maqola (Original Research Article)</li>
            <li>Sharh maqola (Review Article)</li>
          </ul>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ochiqlik</h4>
          <p class="mb-4">Jurnalning Open Select dasturi orqali siz mazkur jurnalda ochiqlik huquqi asosidagi ilmiy-metodik maqolangizni nashr qilish imkoniyatiga ega bo'lasiz. “Ochiqlik” siyosati maqolangiz chop etilgandan so'ng uning darhol onlayn rejimda mavjud bo'lishini ta'minlaydi.</p>
          <p class="mb-0">Bu tadqiqotingizning keng miqyosda ko'rilishi, o'quvchilarining soni va ta'sir doirasining ortishiga zamin yaratadi. Maqolangizga ochiqlik huquqini berish uchun sizdan maqola nashr qilish to'lovini amalga oshirishingiz so'raladi va bu xarajatlar ko'pincha muassasangiz yoki moliyachi tomonidan qoplanishi mumkin.</p>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ekspertizadan o'tkazish va etika talablari</h4>
          <p class="mb-4"><strong>“Filologiya masalalari”</strong> elektron ilmiy-metodik jurnali nashriyoti ekspertlar bahosining yaxlitligiga sodiqdir va qo'lyozmalarni tekshirish jarayonlarining eng yuqori standartlarini qo'llab-quvvatlaydi.</p>
          <p class="mb-0">Maqolangiz muharrir tomonidan yaroqliligi baholangandan so'ng, u ikkita mustaqil, anonim taqrizchilar tomonidan ikki marta anonim tekshiruvdan o'tadi. Tekshiruv davomida nimani kutish mumkinligi haqida ko'proq bilib oling va nashr etikasi bo'yicha ko'rsatmalarimizni o'qing.</p>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Qo'lyozmangizni tayyorlash</h4>
          <p class="mb-3 font-semibold">Maqola uchun umumiy talablar</p>
          <ul class="list-disc list-inside space-y-2">
            <li>Quyidagi elementlar qat'iy ketma-ketlikda yozilishi kerak: sarlavha 3 tilda (o'zbek, rus va ingliz); annotatsiya va kalit so'zlar ham 3 tilda; asosiy matn IMRAD tartibida - INTRODUCTION, METHODS, RESULTS AND DISCUSSION; (minnatdorchilik, manfaatlar deklaratsiyasi, tavsiyalar - ixtiyoriy); ilovalar; sarlavhalar bilan jadvallar (alohida sahifalarda); raqamlar; kerakli hollarda rasm taglavhalari (ro'yxat shaklida).</li>
            <li>Annotatsiya 3 tilda (o'zbek, rus va ingliz) 250-300 ta so'zdan iborat bo'lib, tadqiqot maqsadi, yangiligi, usullari, asosiy natijalari va xulosalarini aks ettirishi kerak.</li>
            <li>Kalit so'zlar 3 tilda (o'zbek, rus va ingliz) 8-10 tadan oshmasligi lozim.</li>
            <li>Asosiy matn kirishdan xulosagacha 4000-7000 ta so'zdan iborat bo'lishi kerak (annotatsiya va kalit so'zlar bu hisobga kirmaydi).</li>
            <li>Foydalanilgan adabiyotlar 30-60 ta bo'lishi, lotin alifbosida va ingliz tilidagi tarjimasi (agar qo'lyozma ingliz tilida bo'lmasa) bilan berilishi lozim.</li>
          </ul>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Maqola turlari</h4>

          <div class="space-y-5">
            <div>
              <h5 class="font-semibold mb-2">1. Original Research Article (original ilmiy maqola)</h5>
              <p class="mb-3">Muallif tomonidan ilk bor o'tkazilgan empirik tadqiqot natijalariga asoslangan maqola. Muallif ma'lumotlarni mustaqil yig'adi, tahlil qiladi va xulosa chiqaradi. IMRAD tarkibiy bo'limlari nomlari <strong>TO'LIQ BOSH HARFLARDA</strong> yoziladi.</p>

              <p class="mb-2 font-semibold">INTRODUCTION (KIRISH)</p>
              <ul class="list-disc list-inside space-y-1 mb-2">
                <li>tadqiqot mavzusining dolzarbligi</li>
                <li>ilmiy muammoning qo'yilishi</li>
                <li>mavjud tadqiqotlar bo'yicha qisqa sharh</li>
                <li>ilmiy bo'shliqni aniqlash (research gap)</li>
                <li>tadqiqotning maqsad va vazifalari</li>
                <li>gipoteza (mavjud bo'lsa)</li>
              </ul>
              <p class="mb-3"><strong>Natija:</strong> mazkur tadqiqot zarurligini asoslash.</p>

              <p class="mb-2 font-semibold">METHODS (TADQIQOT METODLARI)</p>
              <ul class="list-disc list-inside space-y-1 mb-2">
                <li>tadqiqot dizayni (eksperimental, korrelyatsion, korpus tahlili va boshqalar)</li>
                <li>tadqiqot obyekti va predmeti</li>
                <li>ma'lumot yig'ish metodlari: so'rovnoma, intervyu, kuzatish, matn/korpus tahlili</li>
                <li>tanlanma tavsifi: hajmi va parametrlari</li>
                <li>tahlil metodlari: statistik (SPSS, R va boshqalar), lingvistik/kognitiv</li>
                <li>ishonchlilik va validlik masalalari</li>
              </ul>
              <p class="mb-3"><strong>Natija:</strong> tadqiqotni to'liq qayta takrorlash imkoniyati.</p>

              <p class="mb-2 font-semibold">RESULTS (NATIJALAR)</p>
              <ul class="list-disc list-inside space-y-1 mb-2">
                <li>asosiy empirik natijalar</li>
                <li>jadval, grafik va diagrammalar (mavjud bo'lsa)</li>
                <li>statistik ko'rsatkichlar</li>
                <li>aniqlangan qonuniyatlar</li>
              </ul>
              <p class="mb-3"><strong>Muhim:</strong> faqat "nima natija olindi?" savoliga javob.</p>

              <p class="mb-2 font-semibold">DISCUSSION (MUNOZARA)</p>
              <ul class="list-disc list-inside space-y-1 mb-2">
                <li>natijalarni izohlash</li>
                <li>oldingi tadqiqotlar bilan taqqoslash</li>
                <li>gipotezaning tasdiqlanishi yoki rad etilishi</li>
                <li>nazariy ahamiyati</li>
                <li>amaliy ahamiyati</li>
                <li>tadqiqot cheklovlari</li>
                <li>keyingi tadqiqot istiqbollari</li>
              </ul>
              <p class="mb-3">Bu yerda ishning ilmiy qiymati ochib beriladi.</p>

              <p class="mb-2 font-semibold">CONCLUSION (XULOSA)</p>
              <p class="mb-2">(IMRAD tarkibiga kirmaydi, lekin majburiy)</p>
              <ul class="list-disc list-inside space-y-1">
                <li>yakuniy xulosalar</li>
                <li>ilmiy yangilik</li>
                <li>qisqa umumlashtirish</li>
                <li>iqtiboslarsiz</li>
              </ul>
            </div>

            <div>
              <h5 class="font-semibold mb-2">2. Review Article (sharh ilmiy maqola)</h5>
              <p class="mb-3">Muayyan ilmiy yo'nalish bo'yicha avval chop etilgan tadqiqotlarni tizimli tahlil qilish, taqqoslash va umumlashtirishni o'z ichiga olgan maqola. Muallif yangi empirik ma'lumotlar yig'maydi, balki mavjud ilmiy ishlar asosida nazariy va metodologik xulosalar chiqaradi.</p>

              <p class="mb-2 font-semibold">INTRODUCTION (KIRISH)</p>
              <ul class="list-disc list-inside space-y-1 mb-2">
                <li>ilmiy yo'nalishning dolzarbligi</li>
                <li>sharh zarurligini asoslash</li>
                <li>muammoning qo'yilishi</li>
                <li>sharhning maqsadi</li>
              </ul>
              <p class="mb-3">Ilmiy bo'shliqni ko'rsatish majburiy.</p>

              <p class="mb-2 font-semibold">METHODS (TADQIQOT METODLAR)</p>
              <p class="mb-2">Ko'pincha e'tibordan chetda qoladi, lekin majburiy hisoblanadi.</p>
              <ul class="list-disc list-inside space-y-1 mb-2">
                <li>manbalarni tanlash mezonlari: vaqt oralig'i, ma'lumotlar bazalari (Scopus, Web of Science va boshqalar)</li>
                <li>qidiruv strategiyasi (kalit so'zlar)</li>
                <li>kiritish/chiqarib tashlash mezonlari</li>
                <li>tahlil metodlari: tematik tahlil, meta-tahlil (mavjud bo'lsa)</li>
              </ul>
              <p class="mb-3">Sharhning ilmiy asoslanganligini ta'minlaydi.</p>

              <p class="mb-2 font-semibold">RESULTS (NATIJALAR)</p>
              <p class="mb-2">Bu yerda empirik ma'lumotlar emas, balki adabiyotlar tahlili natijalari taqdim etiladi.</p>
              <ul class="list-disc list-inside space-y-1 mb-2">
                <li>asosiy ilmiy yondashuvlar</li>
                <li>nazariy maktablar</li>
                <li>tadqiqotlardagi qarama-qarshiliklar</li>
                <li>zamonaviy tendensiyalar</li>
                <li>taqqoslovchi jadvallar</li>
              </ul>
              <p class="mb-3">Mavzu bo'yicha "ilmiy manzara" shakllantiriladi.</p>

              <p class="mb-2 font-semibold">DISCUSSION (MUNOZARA)</p>
              <p class="mb-2">Asosiy analitik bo'lim.</p>
              <ul class="list-disc list-inside space-y-1 mb-3">
                <li>adabiyotlar asosida umumlashtirilgan xulosalar</li>
                <li>mavjud yondashuvlarni baholash</li>
                <li>ilmiy bo'shliqlarni aniqlash</li>
                <li>muammoli jihatlar</li>
                <li>keyingi tadqiqot istiqbollari</li>
              </ul>

              <p class="mb-2 font-semibold">CONCLUSION (XULOSA)</p>
              <p class="mb-2">(IMRAD tarkibiga kirmaydi, lekin majburiy)</p>
              <ul class="list-disc list-inside space-y-1">
                <li>yakuniy umumlashtirishlar</li>
                <li>nazariy xulosalar</li>
                <li>tavsiyalar</li>
                <li>iqtiboslarsiz</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Formatsiz topshirish</h4>
          <p class="mb-4">Mualliflar o'z qo'lyozmalarini har qanday ilmiy formatda yoki tartibda taqdim etishlari mumkin. Qo'lyozmalar bitta yoki bir nechta fayl shaklida taqdim etilishi, bular Word (DOC yoki DOCX) fayllari bo'lishi mumkin. Tasvirlar va jadvallar matn ichida joylashtirilishi yoki alohida hujjatlar sifatida taqdim etilishi mumkin. Rasmlar tushunilishini ta'minlash uchun yetarli aniqlikda bo'lishi kerak.</p>
          <ul class="list-disc list-inside space-y-2 mb-4">
            <li>Qat'iy formatlash talablari mavjud emas, lekin barcha qo'lyozmalar uning dastlabki baholanishi uchun zarur bo'lgan muhim elementlarni o'z ichiga olishi kerak: annotatsiya, muallif haqidagi asosiy ma'lumotlar (I.F.Sh., lavozim, ilmiy daraja, elektron pochta, telefon raqami 3 tilda), tasvirlar, jadval va ilovalar. Qo'shimcha ma'lumotlar qo'lyozma qabul qilinganidan keyin so'ralishi mumkin.</li>
            <li>Foydalanilgan adabiyotlar ro'yxati APA (American Psychological Association) uslubida tartibga solingan holda yuborilishi lozim.</li>
          </ul>
          <p class="mb-0">E'tibor bering, asl nusxaning fayl formatidan qat'iy nazar, maqolaning tahrirlanadigan versiyasi qayta ko'rib chiqish bosqichida taqdim etilishi kerak.</p>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tekshirish ro'yxati: nimalarni o'z ichiga olishi kerak?</h4>
          <ol class="list-decimal list-inside space-y-3">
            <li><strong>Muallif haqidagi tafsilotlar.</strong> Iltimos, ro'yxatdagi barcha mualliflar “Filologiya masalalari” elektron ilmiy-metodik jurnalining mualliflik mezonlariga mos kelishiga ishonch hosil qiling. Barcha mualliflar qo'lyozmaning muqova sahifasida o'zlarining to'liq ism-shariflari, lavozimlari, ilmiy darajalari, elektron pochta, telefon raqamlarini ko'rsatishlari kerak. Agar mavjud bo'lsa, ORCID, Google Scholar va Scopus havolalarini ham qo'shing. Agar nomlari ko'rsatilgan hammualliflardan birortasi o'zaro ko'rib chiqish jarayonida a'zolikni o'zgartirsa, yangi kerakli mualliflar izoh sifatida ko'rsatilishi mumkin. E'tibor bering, maqolangiz nashr qilinganidan keyin mazkur tafsilotlarga hech qanday o'zgartirish kiritib bo'lmaydi.</li>
            <li><strong>Tasvirlar.</strong> Rasmlar yuqori sifatli bo'lishi kerak (chiziqli tasvir uchun 1200 dpi, kulrang rang uchun 600 dpi va rangli uchun 300 dpi, to'g'ri o'lchamda). Rasmlar jurnal tahririyati tomonidan tanlangan fayl formatlaridan birida taqdim etilishi kerak: EPS, PS, JPEG, TIFF yoki Microsoft Word (DOC yoki DOCX) fayllari Wordda chizilgan rasmlar uchun qabul qilinadi.</li>
            <li><strong>Jadvallar.</strong> Jadvallar matndagi narsalarni takrorlashdan ko'ra yangi ma'lumotlarni taqdim etishi kerak. O'quvchilar jadvalni matnga murojaat qilmasdan sharhlay olishlari kerak. Iltimos, tahrirlanadigan fayllarni taqdim eting.</li>
            <li><strong>Tenglamalar.</strong> Agar siz qo'lyozmangizni Word hujjati sifatida topshirayotgan bo'lsangiz, tenglamalarni tahrirlash mumkinligiga ishonch hosil qiling.</li>
          </ol>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Uchinchi tomon materiallaridan foydalanish</h4>
          <p class="mb-4">Maqolada uchinchi tomon materiallaridan qayta foydalanish uchun kerakli ruxsatni olishingiz kerak. Matnning qisqacha parchalari va boshqa ayrim turdagi materiallardan rasmiy ruxsatisiz tanqid va ko'rib chiqish maqsadida cheklangan miqdorda foydalanishga odatda ruxsat etiladi.</p>
          <p class="mb-0">Maqolangizga mualliflik huquqi sizga tegishli bo'lmagan va ushbu norasmiy shartnoma bilan ta'minlanmagan har qanday materialni kiritmoqchi bo'lsangiz, yuborishdan oldin mualliflik huquqi egasidan yozma ruxsat olishingiz kerak bo'ladi.</p>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Qo'lyozmangizni topshirish</h4>
          <p class="mb-4">Ushbu jurnal topshirish jarayonini boshqarish uchun maxsus portaldan foydalanadi. Taqdimot portali sizga “Filologiya masalalari” elektron ilmiy-metodik jurnali portfeli bo'ylab yuborilgan xabarlaringizni bir joyda ko'rish imkonini beradi. Qo'lyozmangizni yuborish uchun bu yerni bosing.</p>
          <p class="mb-4">Esda tutingki, “Filologiya masalalari” elektron ilmiy-metodik jurnali nashriyoti dastlabki texnik talablarga javob bergan qo'lyozmalarni tekshirish uchun antiplagiat.ru dan foydalanadi. Qo'lyozmangizni «Filologiya masalalari» elektron ilmiy-metodik jurnali tahririyatiga yuborish orqali siz ekspertiza va taqrizlash jarayonlarida originallikni tekshirishga rozilik bildirasiz.</p>
          <p class="mb-0">Qabul qilingandan so'ng, qabul qilingan qo'lyozma nusxasini saqlashingizni tavsiya qilamiz.</p>
        </section>

        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Nashr to'lovi</h4>
          <p class="mb-0">“Filologiya masalalari” elektron ilmiy-metodik jurnalida bir yilda bir marta maqola nashr qilish narxi O'zbekiston Respublikasi fuqarolari uchun <strong>600 000 (olti yuz ming) so'm</strong>. Boshqa mualliflar uchun esa <strong>100 (yuz) AQSH dollari</strong>ni tashkil qiladi.</p>
        </section>

        <section>
          <h4 class="text-lg font-semibold mb-3">Mualliflik huquqi imkoniyatlari</h4>
          <p class="mb-4">Mualliflik huquqi sizga asl materialingizni himoya qilish va maqolangizdan boshqalarning ruxsatingizsiz foydalanishining oldini olish imkoniyatini beradi. “Filologiya masalalari” elektron ilmiy-metodik jurnali turli xil litsenziyalar va qayta foydalanish imkoniyatlarini taklif etadi, shu jumladan ochiq foydalanish uchun nashr qilish uchun Creative Commons lisenziyalari.</p>
          <p class="mb-0">Agar sizda biron bir savol yuzaga kelsa, iltimos biz bilan bog'laning: <a href="mailto:philologymatters@uzswlu.uz" class="text-fmmain hover:underline">philologymatters@uzswlu.uz</a>.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Инструкции для авторов</h4>
          <p class="mb-4">Благодарим вас за выбор электронного научно-методического журнала <strong>«Вопросы филологии»</strong> для публикации вашей рукописи. Настоящие инструкции разработаны для корректной организации процессов двойного слепого рецензирования, редакционной подготовки и публикации.</p>
          <p class="mb-0">Пожалуйста, внимательно ознакомьтесь с требованиями, чтобы рукопись полностью соответствовала стандартам журнала.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Содержание</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>О журнале</li>
            <li>Открытый доступ (Open Access)</li>
            <li>Рецензирование и требования этики</li>
            <li>Подготовка рукописи</li>
            <li>Типы статей</li>
            <li>Подача без жесткого форматирования</li>
            <li>Услуги редактирования</li>
            <li>Проверочный список</li>
            <li>Использование материалов третьих лиц</li>
            <li>Подача рукописи</li>
            <li>Плата за публикацию</li>
            <li>Авторские права и лицензирование</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">О журнале</h4>
          <p class="mb-4"><strong>«Вопросы филологии»</strong> - электронный научно-методический журнал, публикующий оригинальные и качественные исследования.</p>
          <p class="mb-4">Журнал принимает статьи на всех языках. Поддерживаются следующие типы публикаций:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Original Research Article (оригинальная исследовательская статья)</li>
            <li>Review Article (обзорная статья)</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Открытый доступ (Open Access)</h4>
          <p class="mb-4">Через программу Open Select авторы могут публиковать статьи в режиме открытого доступа. Это обеспечивает немедленную онлайн-доступность публикации, расширяет аудиторию и повышает научное влияние работы.</p>
          <p class="mb-0">При выборе открытого доступа взимается публикационный сбор. Во многих случаях эти расходы могут покрываться организацией автора или финансирующей стороной.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Рецензирование и требования этики</h4>
          <p class="mb-4">Издательство журнала <strong>«Вопросы филологии»</strong> придерживается высоких стандартов научной экспертизы и публикационной этики.</p>
          <p class="mb-0">После первичной редакционной проверки рукопись направляется двум независимым анонимным рецензентам и проходит процедуру <strong>двойного слепого рецензирования</strong>. Авторы обязаны соблюдать принципы публикационной этики на всех этапах.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Подготовка рукописи</h4>
          <p class="mb-4">Рукопись должна быть оформлена в четкой последовательности:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Заголовок на 3 языках: узбекском, русском и английском.</li>
            <li>Аннотация и ключевые слова на 3 языках: узбекском, русском и английском.</li>
            <li>Основной текст в порядке IMRAD: <strong>INTRODUCTION</strong>, <strong>METHODS</strong>, <strong>RESULTS</strong>, <strong>DISCUSSION</strong>.</li>
            <li>Опционально: благодарности, декларация интересов, рекомендации.</li>
            <li>Приложения.</li>
            <li>Таблицы с заголовками (при необходимости на отдельных страницах).</li>
            <li>Рисунки и, при необходимости, отдельный список подписей к рисункам.</li>
          </ul>
          <ul class="list-disc list-inside space-y-1">
            <li>Аннотация: 250-300 слов на каждом языке с отражением цели, новизны, методов, основных результатов и выводов.</li>
            <li>Ключевые слова: не более 8-10 на каждом языке.</li>
            <li>Объем основного текста (от введения до заключения): 4000-7000 слов (без аннотации и ключевых слов).</li>
            <li>Список литературы: 30-60 источников в латинице, с английским переводом библиографических данных при необходимости для неанглоязычных рукописей.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Типы статей</h4>
          <div class="space-y-4">
            <div>
              <h5 class="font-semibold mb-2">1. Original Research Article (оригинальная научная статья)</h5>
              <p class="mb-3">Статья, основанная на результатах самостоятельно проведенного эмпирического исследования. Названия разделов IMRAD указываются <strong>ПРОПИСНЫМИ БУКВАМИ</strong>.</p>
              <ul class="list-disc list-inside space-y-2">
                <li><strong>INTRODUCTION (ВВЕДЕНИЕ):</strong> актуальность темы, постановка научной проблемы, краткий обзор литературы, выявление научного пробела (research gap), цели и задачи, гипотеза (при наличии).</li>
                <li><strong>METHODS (МЕТОДЫ ИССЛЕДОВАНИЯ):</strong> дизайн исследования, объект и предмет, методы сбора данных (опрос, интервью, наблюдение, текстовый/корпусный анализ), описание выборки (объем и параметры), методы анализа (SPSS, R, лингвистические/когнитивные), надежность и валидность.</li>
                <li><strong>RESULTS (РЕЗУЛЬТАТЫ):</strong> только фактические результаты, таблицы/графики/диаграммы (при наличии), статистические показатели, выявленные закономерности.</li>
                <li><strong>DISCUSSION (ОБСУЖДЕНИЕ):</strong> интерпретация результатов, сопоставление с предыдущими исследованиями, подтверждение или опровержение гипотезы, теоретическая и практическая значимость, ограничения и перспективы дальнейших исследований.</li>
                <li><strong>CONCLUSION (ЗАКЛЮЧЕНИЕ)</strong> (вне IMRAD, но обязательно): итоговые выводы, научная новизна, краткое обобщение, без цитирования.</li>
              </ul>
            </div>
            <div>
              <h5 class="font-semibold mb-2">2. Review Article (обзорная статья)</h5>
              <p class="mb-3">Статья, включающая системный анализ, сопоставление и обобщение ранее опубликованных исследований по определенному научному направлению. Сбор новых эмпирических данных не требуется.</p>
              <ul class="list-disc list-inside space-y-2">
                <li><strong>INTRODUCTION (ВВЕДЕНИЕ):</strong> актуальность направления, обоснование необходимости обзора, постановка проблемы, цель обзора и обязательное указание научного пробела.</li>
                <li><strong>METHODS (МЕТОДЫ ИССЛЕДОВАНИЯ):</strong> критерии отбора источников, временной диапазон, базы данных (Scopus, Web of Science и др.), поисковая стратегия (ключевые слова), критерии включения/исключения, методы анализа (тематический анализ, мета-анализ при наличии).</li>
                <li><strong>RESULTS (РЕЗУЛЬТАТЫ):</strong> основные научные подходы, теоретические школы, противоречия в исследованиях, современные тенденции, сравнительные таблицы.</li>
                <li><strong>DISCUSSION (ОБСУЖДЕНИЕ):</strong> обобщенные выводы по литературе, оценка существующих подходов, выявление научных пробелов, проблемные аспекты, перспективы дальнейших исследований.</li>
                <li><strong>CONCLUSION (ЗАКЛЮЧЕНИЕ)</strong> (вне IMRAD, но обязательно): итоговые обобщения, теоретические выводы, рекомендации, без цитирования.</li>
              </ul>
            </div>
          </div>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Подача без жесткого форматирования</h4>
          <p class="mb-4">На первичном этапе авторы могут подавать рукописи в любом научном формате или структуре. Подача возможна одним или несколькими файлами, обычно в формате Word (DOC или DOCX). Таблицы и рисунки могут быть встроены в текст или приложены отдельно.</p>
          <p class="mb-4">Жесткие требования к оформлению на первом этапе отсутствуют, однако рукопись должна содержать ключевые элементы для первичной оценки: аннотацию, основные сведения об авторе (Ф.И.О., должность, ученая степень, email, телефон на 3 языках), рисунки, таблицы и приложения.</p>
          <p class="mb-0">Список литературы необходимо оформить по стандарту <strong>APA</strong>. Независимо от исходного формата файла, на этапе доработки должна быть предоставлена редактируемая версия.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Услуги редактирования</h4>
          <p class="mb-4">Издательство журнала <strong>«Вопросы филологии»</strong> предоставляет дополнительные редакционные услуги для повышения качества рукописи перед подачей.</p>
          <p class="mb-0">Услуги могут включать языковую редактуру (в том числе английского текста), исправление орфографии и грамматики, а также техническое форматирование. Для уточнения перечня услуг и стоимости свяжитесь с редакцией.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Проверочный список: что должно быть включено</h4>
          <ol class="list-decimal list-inside space-y-3">
            <li><strong>Сведения об авторах:</strong> все указанные авторы должны соответствовать критериям авторства журнала. На титульной странице обязательно указываются полные Ф.И.О., должность, ученая степень, email, телефон. При наличии добавьте ссылки ORCID, Google Scholar и Scopus. Важно: после публикации изменение этих данных не допускается.</li>
            <li><strong>Иллюстрации:</strong> изображения должны быть высокого качества (1200 dpi для штриховой графики, 600 dpi для полутоновых изображений, 300 dpi для цветных). Допустимые форматы: EPS, PS, JPEG, TIFF или Word (DOC/DOCX для рисунков, созданных в Word).</li>
            <li><strong>Таблицы:</strong> таблицы должны дополнять текст, а не дублировать его; они должны быть понятны без обращения к основному тексту. Предоставляйте редактируемые файлы таблиц.</li>
            <li><strong>Формулы:</strong> при подаче рукописи в Word формулы должны оставаться редактируемыми.</li>
          </ol>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Использование материалов третьих лиц</h4>
          <p class="mb-4">Для повторного использования материалов третьих лиц необходимо получить соответствующие разрешения. В отдельных случаях допускается ограниченное использование коротких фрагментов текста для критического анализа без формального разрешения.</p>
          <p class="mb-0">Если в статье используются материалы, авторские права на которые вам не принадлежат и которые не подпадают под исключения, до подачи рукописи требуется письменное разрешение правообладателя.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Подача рукописи</h4>
          <p class="mb-4">Журнал использует специальный портал для управления процессом подачи и сопровождения рукописей. Через портал можно отслеживать все отправленные материалы в едином интерфейсе.</p>
          <p class="mb-4">Рукописи, прошедшие первичные технические требования, проверяются на оригинальность с помощью <strong>antiplagiat.ru</strong>. Отправляя рукопись, вы подтверждаете согласие на проверку оригинальности в рамках рецензирования и редакционной обработки.</p>
          <p class="mb-0">После принятия статьи рекомендуется сохранить копию принятой версии рукописи.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Плата за публикацию</h4>
          <p class="mb-0">Стоимость публикации одной статьи в журнале <strong>«Вопросы филологии»</strong> один раз в год составляет <strong>600 000 сумов</strong> для граждан Республики Узбекистан и <strong>100 долларов США</strong> для остальных авторов.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Авторские права и лицензирование</h4>
          <p class="mb-4">Авторское право защищает ваш оригинальный материал и предотвращает несанкционированное использование статьи. Журнал предлагает различные варианты лицензирования и повторного использования, включая лицензии <strong>Creative Commons</strong> для публикаций в открытом доступе.</p>
          <p class="mb-0">По вопросам обращайтесь: <a href="mailto:philologymatters@uzswlu.uz" class="text-fmmain hover:underline">philologymatters@uzswlu.uz</a>.</p>
        </section>
        '''
    },
    'editorial_policy': {
        'title': 'Editorial Policy',
        'title_uz': 'Tahririyat siyosati',
        'title_ru': 'Редакционная политика',
        'content': '''
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
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahririyat siyosati haqida</h4>
          <p class="mb-4">Quyidagi qoidalar <strong>“Filologiya masalalari”</strong> elektron ilmiy-metodik jurnaliga tegishli. Iltimos, maqolangizni yuborishdan oldin ushbu siyosatni to'liq o'qib chiqing.</p>
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
        ''',
        'content_ru': '''
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
        '''
    },
    'site_editing_services': {
        'title': 'Site Editing Services',
        'title_uz': 'Sayt tahrirlash xizmatlari',
        'title_ru': 'Услуги редактирования сайта',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Editing Services</h4>
          <p class="mb-0">Language editing, stylistic revision, formatting, and bibliographic checking services are available to authors. These services are optional and do not guarantee acceptance for publication.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Types of Support</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Spelling and stylistic editing to improve language quality</li>
            <li>Formatting in line with journal design and submission requirements</li>
            <li>Standardization of table and figure captions</li>
            <li>Reference-list checking</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">How to Request the Service</h4>
          <p class="mb-0">When editing support is requested, the editorial office reviews the scope of work and turnaround time and then provides details separately.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Tahrirlash xizmatlari</h4>
          <p class="mb-0">Mualliflar uchun til va uslubiy tahrir, formatlash va bibliografik tekshiruv xizmatlari taklif etiladi. Xizmatlar ixtiyoriy bo'lib, maqolaning nashrga qabul qilinishini kafolatlamaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Xizmat turlari</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Imlo va uslubiy tahrir (til sifati)</li>
            <li>Formatlash va dizayn talablariga moslashtirish</li>
            <li>Jadval va rasm yozuvlarini standartlashtirish</li>
            <li>Adabiyotlar ro'yxatini tekshirish</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Qanday foydalaniladi</h4>
          <p class="mb-0">Tahrirlash xizmati talab qilinganda, tahririyat ish hajmi va muddatini baholab, alohida tartibda ma'lumot beradi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Редакционные услуги</h4>
          <p class="mb-0">Авторам доступны услуги языкового и стилистического редактирования, форматирования и библиографической проверки. Эти услуги являются дополнительными и не гарантируют принятие статьи к публикации.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Виды поддержки</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Орфографическое и стилистическое редактирование</li>
            <li>Форматирование в соответствии с требованиями журнала</li>
            <li>Стандартизация подписей к таблицам и рисункам</li>
            <li>Проверка списка литературы</li>
          </ul>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Как заказать услугу</h4>
          <p class="mb-0">Если автор запрашивает редакционную помощь, редакция оценивает объем работы и сроки выполнения, после чего предоставляет подробную информацию отдельно.</p>
        </section>
        '''
    },
    'journal_metrics': {
        'title': 'Journal Metrics',
        'title_uz': 'Jurnal ko\'rsatkichlari',
        'title_ru': 'Показатели журнала',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Journal Metrics</h4>
          <div class="space-y-4 text-gray-700">
            <div>
              <div class="font-medium text-gray-900">Usage</div>
              <p class="mt-1">On average, journal content is viewed or downloaded several thousand times each year.</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Citation Indicators</div>
              <p class="mt-1">Citation-related indicators are updated in line with the journal's latest reporting cycle.</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Speed and Acceptance</div>
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li>5 days: submission to first editorial decision.</li>
                <li>9 days: submission to decision after peer review.</li>
                <li>18 days: submission to acceptance.</li>
                <li>5 days: acceptance to online publication.</li>
              </ul>
            </div>
          </div>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Understanding and Using Journal Metrics</h4>
          <p class="mb-4">Journal metrics can help readers and authors decide whether a publication is a suitable venue for their work. However, no single metric can fully represent the quality or impact of a journal.</p>
          <p class="mb-4">Each indicator has limits and should never be interpreted in isolation. Metrics should support qualitative evaluation rather than replace it. We recommend considering them alongside the journal's aims, scope, readership, and previously published content.</p>
          <p class="mb-0">In addition, each article should be judged on its own scholarly value, not only on the reputation or performance of the journal where it appears.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">About These Metrics</h4>
          <p class="mb-0">Usage and acceptance data are based on the latest complete calendar year and are typically refreshed annually. Speed-related data can be updated on a rolling basis, while citation indicators may be refreshed later in the year depending on source availability.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlari</h4>
          <div class="space-y-4 text-gray-700">
            <div>
              <div class="font-medium text-gray-900">Foydalanish</div>
              <p class="mt-1">Yillik o'rtacha 400 ming marta ko'riladi yoki yuklab olinadi.</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Iqtibos ko'rsatkichlari</div>
              <p class="mt-1">Crossref, Web of Science va Scopus bo'yicha jami iqtiboslar soni: 500 +</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Maqolaning o'rtacha e'lon qilinish muddatlari</div>
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li>dastlabki texnik mosligi bo'yicha qarorgacha bo'lgan muddat 5 kun;</li>
                <li>taqdim etishdan boshlab birinchi tahririy qarorga qadar taxminan 7 kun;</li>
                <li>ko'rib chiqishdan so'ng birinchi qarorni topshirishgacha taxminan 8 kun;</li>
                <li>qabul qilingan kundan boshlab Internetda nashrga qadar o'rtacha 6 kun;</li>
                <li>qabul qilish darajasi 12%.</li>
              </ul>
            </div>
          </div>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlarini tushunish va ulardan foydalanish</h4>
          <p class="mb-4">Jurnal ko'rsatkichlari o'quvchilar va o'zlarining keyingi qo'lyozmalarini nashr qilish uchun qayerga topshirishni hal qilayotgan mualliflar uchun foydali vosita bo'lishi mumkin. Biroq, har qanday o'lchov jurnalning sifati va ta'siri haqidagi ma'lumotlarning faqat bir qismini aks ettiradi. Har bir ko'rsatkichning o'z cheklovlari mavjud, ya'ni uni hech qachon alohida ko'rib chiqmaslik kerak va ko'rsatkichlar sifat tahlilini almashtirish uchun emas, balki qo'llab-quvvatlash uchun ishlatilishi kerak.</p>
          <p class="mb-0">Jurnalning maqsadlari va qamrovi, uning o'quvchilar soni va jurnalda chop etilgan oldingi kontentni ko'rib chiqish kabi boshqa sifat omillari bilan bir qatorda har doim bir qator ko'rsatkichlardan foydalanishingizni qat'iy tavsiya qilamiz. Bundan tashqari, individual maqola har doim nashr etilgan jurnalning samaradorligiga emas, balki uning mohiyatiga qarab baholanishi kerak.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Jurnal ko'rsatkichlari haqida qisqacha</h4>
          <p class="mb-0">Yuqoridagi foydalanish va qabul qilish ma'lumotlari eng so'nggi to'liq kalendar yili uchun va har yili fevral oyida yangilanadi. Tezlik ma'lumotlari har olti oyda oldingi olti oylik ma'lumotlar asosida yangilanadi. Iqtibos stavkalari har yili yilning o'rtalarida yangilanadi. E'tibor bering, ba'zi jurnallar quyidagi ko'rsatkichlarning hammasini ko'rsatmaydi (sababini bilib oling).</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Показатели журнала</h4>
          <div class="space-y-4 text-gray-700">
            <div>
              <div class="font-medium text-gray-900">Использование</div>
              <p class="mt-1">В среднем материалы журнала просматриваются или скачиваются несколько тысяч раз в год.</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Показатели цитирования</div>
              <p class="mt-1">Показатели, связанные с цитированием, обновляются в соответствии с последним циклом отчетности журнала.</p>
            </div>
            <div>
              <div class="font-medium text-gray-900">Скорость и принятие</div>
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li>5 дней: от подачи статьи до первого редакционного решения.</li>
                <li>9 дней: от подачи до решения после рецензирования.</li>
                <li>18 дней: от подачи до принятия к публикации.</li>
                <li>5 дней: от принятия до публикации онлайн.</li>
              </ul>
            </div>
          </div>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Как понимать и использовать показатели журнала</h4>
          <p class="mb-4">Показатели журнала могут помочь читателям и авторам оценить, подходит ли издание для публикации их работы. Однако ни один показатель не отражает полностью качество и влияние журнала.</p>
          <p class="mb-4">Каждый индикатор имеет свои ограничения и не должен рассматриваться отдельно от других факторов. Метрики должны дополнять качественную оценку, а не заменять ее. Мы рекомендуем рассматривать их вместе с целями журнала, тематическим охватом, аудиторией и ранее опубликованными материалами.</p>
          <p class="mb-0">Кроме того, каждая статья должна оцениваться по собственной научной ценности, а не только по репутации или показателям журнала, в котором она опубликована.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">О данных показателях</h4>
          <p class="mb-0">Данные об использовании и принятии материалов основаны на последнем полном календарном году и обычно обновляются ежегодно. Данные о скорости обработки могут обновляться по скользящему принципу, а показатели цитирования - позднее, по мере появления новых сведений.</p>
        </section>
        '''
    },
    'aims_scope': {
        'title': 'Aims and Scope',
        'title_uz': 'Maqsadlari va qamrovi',
        'title_ru': 'Цели и задачи',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Aims and Scope</h4>
          <p class="mb-0">The journal is devoted to theoretical and applied research in philology and linguistics and promotes contemporary scholarly approaches in these fields.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Main Areas</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>General and comparative linguistics</li>
            <li>Applied linguistics and translation studies</li>
            <li>Literary studies and text analysis</li>
            <li>Discourse and pragmatics research</li>
            <li>Language teaching methodology</li>
            <li>Corpus and digital linguistics</li>
          </ul>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Maqsadlari va qamrovi</h4>
          <p class="mb-4">“Filologiya masalalari” elektron ilmiy-metodik jurnal bo'lib, filologiya (10.00.00) va pedagogika (13.00.00) fanlari chorrahasida bilim, nazariya yoki metodologiyani ilgari suruvchi dunyo bo'ylab olib boriluvchi tadqiqot natijalarini qo'llab-quvvatlaydi.</p>
          <p class="mb-4">Jurnal globallashgan dunyoda birinchi (ona tili), ikkinchi va chet tillarni o'rganish, o'rgatish va egallashda pedagogik masalalar bilan bir qatorda til va boshqa filologik muammolarning roli bilan bog'liq.</p>
          <p class="mb-0">Jurnalda e'lon qilinuvchi tadqiqotlar ilmiy jamoatchilikka o'z tadqiqotlarining asl natijalarini e'lon qilish, filologiya va pedagogika fanlarining istiqbolli va dolzarb yo'nalishlariga e'tiborni jalb qilish, O'zbekiston va xorijiy filologlar o'rtasida ilmiy almashinuv va hamkorlikni rivojlantirish, O'zbekiston hamda xalqaro ilmiy hamjamiyat uchun dolzarb bo'lgan ilmiy tadqiqotlar natijalari va filologiya fanlarini rivojlantirish bo'yicha konstruktiv g'oyalarni, shuningdek, ularni o'qitishning innovasion uslublarini taqdim etish, kitobxonlarni filologiya tadqiqoti sohasidagi O'zbekiston, MDH mamlakatlari va uzoq xorijda ishlab chiqilgan eng so'nggi yo'nalishlar, nazariyalar hamda ularning amaliy qo'llanilishi bilan tanishtirish, til, madaniyat, bilish va muloqotning o'zaro ta'sirini ochib beruvchi fanlararo xarakterdagi keng ko'lamli dolzarb filologik va pedagogik muammolar bo'yicha original ilmiy tadqiqotlar natijalarini nashr etish bilan shug'ullanadi.</p>
        </section>
        <section class="mb-8">
          <p class="mb-4">“Filologiya masalalari” til ta'limining har qanday jihatini o'rganish uchun filologiya va pedagogikaning barcha an'analaridan nazariyalar va metodologiyalarni o'zida mujassam etgan tadqiqotlarni rag'batlantiradi.</p>
          <p class="mb-0">Filologiya va pedagogika chorrahasida o'rganiladigan yo'nalishlar qatoriga, lekin ular bilan cheklanmagan holda quyidagilar kiradi: tilshunoslik, adabiyotshunoslik, tarjimashunoslik, jurnalistika, metodika, pedagogika va psixologiya.</p>
        </section>
        <section class="mb-8">
          <p class="mb-4">“Filologiya masalalari” asl tadqiqotlarga yo'naltirilgan jurnaldir. Maqolalar ta'limga amaliy va siyosiy ta'sir ko'rsatishi mumkin, ammo ular kuchli tadqiqotlarga asoslangan bo'lishi, tahlillari va muhokamalarida kuchli konseptual asosga ega bo'lishi kerak.</p>
          <p class="mb-0">Jurnal sifatli, miqdoriy yoki aralash metodik paradigmalarning prinsipial qo'llanilishini aks ettiruvchi intizomiy va fanlararo tadqiqot an'analariga asoslangan filologiya hamda tegishli mutaxassisliklarning turli yo'nalishlarini qamrab oluvchi eksperimental tadqiqotlar, sharhlovchi maqolalar, amaliy hisobotlar va tadqiqot loyihalarini, jumladan amaliy tadqiqotlar, etnografik sohaga oid izlanishlar, eksperimental/yarim eksperimental tadqiqotlarni qabul qiladi. Maqolalar xalqaro o'quvchilar ommasiga mos bo'lishi kerak.</p>
        </section>
        <section class="mb-8">
          <p class="mb-0">Filologiya va pedagogika fanlarining barcha jihatlariga oid maqolalar mamlakat, jamiyat yoki ta'lim olib borilayotgan hamda dunyoning barcha tillarida bo'lishi mumkin. Bunga ona va ikkinchi tillarni o'rgatish, immersion ta'lim bilan bog'liq masalalar, mazmunli til o'rgatish, ikki tillilik/ko'p tillilik va o'rganish muhitlari kiradi. Biroq til va ta'lim kompetensiyasi xorijiy tillardagi zamonaviy ta'limga (ya'ni, zamonaviy chet tillari yoki chet tili sifatidagi ingliz tili) taalluqli emas.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ikki tomonlama yopiq taqriz siyosati</h4>
          <p class="mb-0">Ushbu jurnaldagi barcha tadqiqot maqolalari dastlabki tahririyat tekshiruvi va ikki tomonlama yopiq taqriz jarayoni asosida jiddiy ekspertizadan o'tkaziladi.</p>
        </section>
        <section>
          <p class="mb-0">Maqolangizni qanday yuborishni bilish uchun <a href="/page/author_instructions" class="text-fmmain hover:underline">mualliflar uchun ko'rsatmalar</a>ni o'qing.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Цели и охват</h4>
          <p class="mb-0">Журнал посвящен теоретическим и прикладным исследованиям в области филологии и лингвистики и продвигает современные научные подходы в этих сферах.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Основные направления</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Общее и сопоставительное языкознание</li>
            <li>Прикладная лингвистика и переводоведение</li>
            <li>Литературоведение и анализ текста</li>
            <li>Исследования дискурса и прагматики</li>
            <li>Методика преподавания языка</li>
            <li>Корпусная и цифровая лингвистика</li>
          </ul>
        </section>
        '''
    },
    'journal_info': {
        'title': 'Journal Information',
        'title_uz': 'Jurnal haqida ma\'lumot',
        'title_ru': 'Информация о журнале',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">About the Journal</h4>
          <p class="mb-0">The journal specializes in publishing scholarly articles in philology, linguistics, and literary studies. Its goal is to promote modern research approaches and strengthen academic cooperation.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Who It Is For</h4>
          <p class="mb-0">The journal is intended for teachers, researchers, doctoral students, and professionals interested in the field.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Publishing Policy</h4>
          <p class="mb-0">Articles are selected on the basis of scholarly review. The reliability of the submitted information and the accuracy of the cited sources are considered essential criteria.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Jurnal haqida</h4>
          <p class="mb-0">Jurnal filologiya, tilshunoslik va adabiyotshunoslik yo'nalishlarida ilmiy maqolalar nashr etishga ixtisoslashgan. Maqsad — zamonaviy ilmiy yondashuvlarni targ'ib qilish va ilmiy hamkorlikni kengaytirish.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Kimlar uchun</h4>
          <p class="mb-0">Jurnal o'qituvchilar, tadqiqotchilar, doktorantlar va sohaga qiziquvchi mutaxassislar uchun mo'ljallangan.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Nashr siyosati</h4>
          <p class="mb-0">Maqolalar ilmiy ekspertiza asosida saralanadi. Mualliflar tomonidan taqdim etilgan ma'lumotlarning ishonchliligi va manbalarining to'g'riligi muhim mezon hisoblanadi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">О журнале</h4>
          <p class="mb-0">Журнал специализируется на публикации научных статей по филологии, лингвистике и литературоведению. Его цель - продвигать современные исследовательские подходы и расширять академическое сотрудничество.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Для кого предназначен журнал</h4>
          <p class="mb-0">Журнал предназначен для преподавателей, исследователей, докторантов и специалистов, интересующихся данной областью.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Издательская политика</h4>
          <p class="mb-0">Статьи отбираются на основе научного рецензирования. Надежность представленных данных и точность приведенных источников являются важнейшими критериями.</p>
        </section>
        '''
    },
    'news_calls': {
        'title': 'News and Calls for Papers',
        'title_uz': 'Yangiliklar va maqolalar uchun chaqiruvlar',
        'title_ru': 'Новости и приглашения к публикации',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">News and Calls</h4>
          <p class="mb-0">This section regularly publishes journal news, calls for special issues, and other important announcements related to editorial activities.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">How to Follow Updates</h4>
          <p class="mb-0">Check the news section regularly and submit your manuscripts in response to active calls whenever relevant.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Yangiliklar va chaqiruvlar</h4>
          <p class="mb-0">Ushbu bo'limda jurnal faoliyatiga oid yangiliklar, maxsus sonlar bo'yicha chaqiruvlar va muhim e'lonlar muntazam joylashtiriladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Qanday kuzatish mumkin</h4>
          <p class="mb-0">Yangiliklar bo'limini tekshirib boring yoki e'lon qilingan chaqiruvlarga muvofiq maqolalaringizni taqdim eting.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Новости и объявления</h4>
          <p class="mb-0">В этом разделе регулярно публикуются новости журнала, приглашения к участию в специальных выпусках и другие важные объявления, связанные с деятельностью редакции.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Как следить за обновлениями</h4>
          <p class="mb-0">Регулярно проверяйте раздел новостей и отправляйте свои материалы в ответ на актуальные объявления и приглашения.</p>
        </section>
        '''
    },
    'conferences': {
        'title': 'Conferences',
        'title_uz': 'Konferentsiyalar',
        'title_ru': 'Конференции',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Conferences</h4>
          <p class="mb-0">Information about academic conferences, roundtables, and seminars organized in cooperation with the journal is published here.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Participation and Publication</h4>
          <p class="mb-0">Papers prepared on the basis of conference materials may be considered separately if they meet the journal's submission requirements.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Konferensiyalar</h4>
          <p class="mb-0">Jurnal hamkorligida o'tkaziladigan ilmiy konferensiyalar, davra suhbatlari va seminarlar haqida ma'lumotlar shu yerda beriladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Ishtirok va nashr</h4>
          <p class="mb-0">Konferensiya materiallari asosida tayyorlangan maqolalar jurnal talablariga mos bo'lsa, alohida ko'rib chiqiladi.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Конференции</h4>
          <p class="mb-0">Здесь публикуется информация о научных конференциях, круглых столах и семинарах, проводимых при сотрудничестве с журналом.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Участие и публикация</h4>
          <p class="mb-0">Статьи, подготовленные на основе материалов конференции, могут рассматриваться отдельно, если они соответствуют требованиям журнала.</p>
        </section>
        '''
    },
    'for_uzgumya_researchers': {
        'title': 'For UzGUMYA Researchers',
        'title_uz': 'UzDJTU tadqiqotchilari uchun',
        'title_ru': 'Для исследователей УзГУМЯ',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">For UzGUMYA Researchers</h4>
          <p class="mb-0">Researchers from the university can receive guidance on the authorship process and methodological support. Topics aligned with internal academic priorities may be recommended separately.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Recommendations</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Registration through an institutional email address is recommended.</li>
            <li>Coordinate the article's topic with your department or academic supervisor.</li>
            <li>Clearly indicate results produced within internal grants and research projects.</li>
          </ul>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">UzDJTU tadqiqotchilari uchun</h4>
          <p class="mb-0">Universitet tadqiqotchilari uchun mualliflik jarayoni bo'yicha maslahat va metodik ko'mak ko'rsatiladi. Ichki ilmiy yo'nalishlarga mos mavzular alohida tavsiya qilinishi mumkin.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tavsiyalar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Muassasa emaili orqali ro'yxatdan o'tish tavsiya etiladi.</li>
            <li>Maqola yo'nalishini kafedra yoki ilmiy rahbar bilan muvofiqlashtiring.</li>
            <li>Ichki grantlar va loyihalar bo'yicha natijalarni alohida ko'rsating.</li>
          </ul>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Для исследователей УзГУМЯ</h4>
          <p class="mb-0">Исследователи университета могут получить консультации по процессу подготовки публикации и методическую поддержку. Темы, соответствующие внутренним научным направлениям, могут рекомендоваться отдельно.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Рекомендации</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Рекомендуется регистрироваться с использованием институциональной электронной почты.</li>
            <li>Согласуйте тему статьи с кафедрой или научным руководителем.</li>
            <li>Отдельно указывайте результаты, полученные в рамках внутренних грантов и проектов.</li>
          </ul>
        </section>
        '''
    },
    'for_all_researchers': {
        'title': 'For All Researchers',
        'title_uz': 'Barcha tadqiqotchilar uchun',
        'title_ru': 'Для всех исследователей',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">For All Researchers</h4>
          <p class="mb-0">The journal is open to researchers from all regions and institutions. Submissions are considered when the topic fits the journal's scope.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Recommendations</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Prepare the manuscript in accordance with the journal requirements.</li>
            <li>Make sure the reference list is complete and accurate.</li>
            <li>Provide open data and supplementary materials whenever possible.</li>
          </ul>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Barcha tadqiqotchilar uchun</h4>
          <p class="mb-0">Jurnal barcha hudud va muassasalardan bo'lgan tadqiqotchilar uchun ochiq. Mavzu jurnal qamroviga mos bo'lsa, maqola ko'rib chiqiladi.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Tavsiyalar</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Maqolani jurnal talablari asosida tayyorlang.</li>
            <li>Adabiyotlar ro'yxatini aniq va to'liq shakllantiring.</li>
            <li>Ochiq ma'lumotlar va ilovalarni iloji boricha taqdim eting.</li>
          </ul>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Для всех исследователей</h4>
          <p class="mb-0">Журнал открыт для исследователей из любых регионов и организаций. Материалы рассматриваются, если их тема соответствует профилю журнала.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Рекомендации</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>Готовьте рукопись в соответствии с требованиями журнала.</li>
            <li>Формируйте список литературы точно и полно.</li>
            <li>По возможности прикладывайте открытые данные и дополнительные материалы.</li>
          </ul>
        </section>
        '''
    }
}

def update_pages(only_missing=False):
    # Initialize database connection
    dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    
    current_time = int(time.time())
    
    # Get all existing pages
    existing_pages = dbc.pages.get().exec()
    existing_aliases = {page['alias']: page for page in existing_pages} if existing_pages else {}
    
    # Update or create each page
    for alias, page_data in PAGES_DATA.items():
        if alias in existing_aliases:
            if only_missing:
                print(f"Skipping existing page: {page_data['title']}")
                continue
            print(f"Updating page: {page_data['title']}")
            dbc.pages.get(alias=alias).update(
                title=page_data['title'],
                title_uz=page_data['title_uz'],
                title_ru=page_data['title_ru'],
                content=page_data['content'],
                content_uz=page_data['content_uz'],
                content_ru=page_data['content_ru'],
                last_update=current_time
            ).exec()
        else:
            print(f"Creating new page: {page_data['title']}")
            dbc.pages.add(
                alias=alias,
                title=page_data['title'],
                title_uz=page_data['title_uz'],
                title_ru=page_data['title_ru'],
                content=page_data['content'],
                content_uz=page_data['content_uz'],
                content_ru=page_data['content_ru'],
                last_update=current_time,
                created_at=current_time
            ).exec()

    print("All pages updated successfully!")


def _parse_args():
    parser = argparse.ArgumentParser(description='Seed/update static pages')
    parser.add_argument(
        '--only-missing',
        action='store_true',
        help='Create only missing pages and keep existing content untouched',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    update_pages(only_missing=args.only_missing)
