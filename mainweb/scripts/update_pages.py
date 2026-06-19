import argparse
import sys
import os
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector


def _env(name, default=''):
    value = os.environ.get(name, default)
    return default if value is None else value


DB_HOST = _env('DB_HOST', 'db')
DB_PORT = int(_env('DB_PORT', '5432'))
DB_USER = _env('DB_USER', 'postgres')
DB_PASSWORD = _env('DB_PASSWORD', '')
DB_NAME = _env('DB_NAME', 'journal2')

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
        'title': 'Guidelines for Authors',
        'title_uz': 'Mualliflar uchun ko\'rsatmalar',
        'title_ru': 'Руководство для авторов',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">I. Preparation of the Manuscript for Publication</h4>
          <p class="mb-4">The manuscript is submitted through the journal's official website: <a href="https://philmatt.uzswlu.uz/" class="text-fmmain hover:underline">https://philmatt.uzswlu.uz/</a>, with each version attached as an individual file. The first version, containing the author's full name, institutional affiliation, and email address, should be saved as: <strong>Surname_manuscript.docx</strong>. The second version, prepared for double-blind peer review and excluding all author information, should be saved under the word "Manuscript": <strong>Manuscript.docx</strong>. In this version, the word "Author" should be used in references to the author's own publications instead of the author's full name.</p>
          <p class="mb-4">The submitted manuscript must not have been previously published in other journals or publications and should present the results of the author's original research, demonstrating its scientific novelty, relevance, and theoretical as well as practical significance.</p>
          <p class="mb-4">All the manuscripts that have passed the technical review are checked using Antiplag.uz or Turnitin.com. Only manuscripts with an originality rate exceeding 80% are accepted for further editorial processing.</p>
          <p class="mb-4">The review process is conducted in accordance with the principles of double-blind peer review. Manuscripts that receive positive reviewer evaluations are forwarded to a journal expert for further editorial preparation prior to publication.</p>
          <p class="mb-0">To ensure compliance with the journal's requirements, authors are assisted by a journal expert throughout the editorial process. The editorial board is committed to maintaining constructive cooperation with authors until a final positive editorial decision is reached. All communication between the author and the editorial board is conducted through the journal expert.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">II. Technical Guidelines for Manuscript Preparation</h4>
          <p class="mb-4">The manuscript should contain 4,000–7,000 words for doctoral students, independent researchers, and academic staff, and 2,500–3,000 words for master's degree students. Manuscripts must be submitted in DOCX format and prepared in Times New Roman font with 1.5 line spacing and 2 cm margins on all sides.</p>
          <p class="mb-4">The title of the manuscript should be centered at the top of the page and typed in 14 pt BOLD UPPERCASE LETTERS without paragraph indentation. No full stop should be placed at the end of the title. The title must be provided in Uzbek, English, and Russian, as well as in the language of the manuscript.</p>
          <p class="mb-4">Below the title, the author's first name, patronymic, and surname should be provided in Uzbek, English, and Russian, as well as in the language of the manuscript, in 14 pt bold font. The number of authors of a single manuscript must not exceed three.</p>
          <p class="mb-4">The following line should contain the full name of the author's (authors') institution, followed by the city and country. On the next line, the email address of the corresponding author should be indicated in 14 pt font. This information must be provided in Uzbek, English, and Russian, as well as in the language of the manuscript. If the authors are affiliated with different institutions, the corresponding affiliation should be specified separately for each author. Only the principal place of work or study of the author(s) should be indicated. The ORCID ID of each author should also be provided. Author information in each language should be presented separately.</p>
          <p class="mb-4">The abstract should be placed below the author information. It must include the relevance of the study, the aims and objectives of the research, the methods employed, the main findings, and the conclusions. The abstract should contain 250–300 words for doctoral students, independent researchers, and academic staff, and 150–200 words for master's degree students. It must be provided in Uzbek, English, and Russian, as well as in the language of the manuscript. The abstract should be formatted in 14 pt font, with 2 cm left and right indents, justified alignment, and a 1 cm first-line paragraph indent. A 1.5-line space should be left after the abstract.</p>
          <p class="mb-4">Below the abstract, 8–10 keywords for doctoral students, independent researchers, and academic staff, and 6–8 keywords for master's degree students should be provided. The keywords should reflect the subject matter of the research and facilitate the retrieval of relevant information. Keywords should be formatted in a 14 pt font, with 2 cm left and right indents and justified alignment. A 1.5-line space should be left after the keywords.</p>
          <p class="mb-0">The main text of the manuscript should be typed in regular 14 pt font. The text should be justified, with a first-line paragraph indent of 1 cm. The journal publishes two types of manuscripts, which must be prepared in accordance with the IMRAD format.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">1. Original Research Article (IMRAD structure)</h4>
          <p class="mb-4">An <strong>Original Research Article</strong> presents the results of an original empirical study conducted by the author(s). In other words, the author independently collects data, analyzes them, and formulates conclusions. The manuscript should include the following sections, with the titles of the IMRAD sections indicated in UPPERCASE LETTERS:</p>
          <p class="mb-2"><strong>INTRODUCTION</strong></p>
          <p class="mb-3">This section should provide the rationale for the study and establish the research context. It should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>the relevance of the research topic;</li>
            <li>formulation of the research question;</li>
            <li>a brief review of existing studies;</li>
            <li>identification of the research gap;</li>
            <li>the aim and objectives of the study;</li>
            <li>the hypothesis (if applicable).</li>
          </ul>
          <p class="mb-4"><em>→ This section should justify the necessity and scholarly significance of the study.</em></p>
          <p class="mb-2"><strong>METHODS</strong></p>
          <p class="mb-3">This section should provide a detailed description of the research procedure sufficient to ensure the transparency and replicability of the study. The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>the research design (experimental, correlational, corpus-based analysis, etc.);</li>
            <li>the object and subject of the research;</li>
            <li>data collection methods: questionnaires; interviews; observation; text or corpus analysis;</li>
            <li>sample characteristics: sample size; sample parameters;</li>
            <li>methods of analysis: statistical methods (SPSS, R, etc.); linguistic or cognitive methods;</li>
            <li>issues of research reliability and validity.</li>
          </ul>
          <p class="mb-4"><em>→ This section should provide sufficient detail to enable replication of the study.</em></p>
          <p class="mb-2"><strong>RESULTS</strong></p>
          <p class="mb-3">This section presents only factual findings without interpretation. The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>the main empirical findings;</li>
            <li>tables, graphs, and charts (if applicable);</li>
            <li>statistical indicators;</li>
            <li>identified patterns and trends.</li>
          </ul>
          <p class="mb-4"><em>→ This section should answer the question: "What results were obtained?"</em></p>
          <p class="mb-2"><strong>DISCUSSION</strong></p>
          <p class="mb-3">This section is devoted to the interpretation of the findings and explains their scholarly significance. The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>interpretation of the findings;</li>
            <li>comparison with previous studies;</li>
            <li>confirmation or refutation of the hypothesis;</li>
            <li>theoretical significance of the study;</li>
            <li>practical significance of the study;</li>
            <li>limitations of the study;</li>
            <li>directions for further research.</li>
          </ul>
          <p class="mb-4"><em>→ This section reveals the scientific significance of the study.</em></p>
          <p class="mb-2"><strong>CONCLUSION</strong> (not included in the IMRAD format but considered a mandatory section)</p>
          <p class="mb-3">The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>the conclusions of the study;</li>
            <li>the scientific novelty of the study;</li>
            <li>a concise summary of the findings.</li>
          </ul>
          <p class="mb-0">Citations should not be included in this section.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">2. Review Article (IMRAD structure)</h4>
          <p class="mb-4">A <strong>Review Article</strong> (review research article or analytical article) presents a systematic analysis, comparison, and synthesis of previously published studies within a particular research field. Unlike an Original Research Article, a Review Article does not involve the collection of new empirical data; instead, it develops theoretical and methodological conclusions based on existing scholarly literature. The manuscript should include the following sections, with the titles of the structural sections indicated in UPPERCASE LETTERS:</p>
          <p class="mb-2"><strong>INTRODUCTION</strong></p>
          <p class="mb-3">The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>the relevance of the research field;</li>
            <li>justification for conducting the review study;</li>
            <li>formulation of the research problem;</li>
            <li>the aim of the review.</li>
          </ul>
          <p class="mb-4"><em>→ Identification of research gaps related to the problem is mandatory.</em></p>
          <p class="mb-2"><strong>METHODS</strong></p>
          <p class="mb-3">The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>criteria for source selection: time period; databases used (Scopus, Web of Science, etc.);</li>
            <li>the search strategy and keywords used;</li>
            <li>inclusion and exclusion criteria for sources;</li>
            <li>methods of analysis: thematic analysis; meta-analysis (if applicable).</li>
          </ul>
          <p class="mb-4"><em>→ This section should ensure the scientific validity and methodological transparency of the review.</em></p>
          <p class="mb-2"><strong>RESULTS</strong></p>
          <p class="mb-3">This section presents the results of the analysis of scholarly literature, not empirical data. The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>the main scientific approaches;</li>
            <li>major theoretical schools;</li>
            <li>contradictions and inconsistencies in previous studies;</li>
            <li>current research trends;</li>
            <li>comparative tables.</li>
          </ul>
          <p class="mb-4"><em>→ This section should provide a comprehensive scholarly overview of the research topic under consideration.</em></p>
          <p class="mb-2"><strong>DISCUSSION</strong></p>
          <p class="mb-3">This section is the main analytical section of the review manuscript. The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>generalized conclusions based on the analysis of the literature;</li>
            <li>critical evaluation of existing approaches;</li>
            <li>identification of research gaps;</li>
            <li>unresolved or problematic issues within the research field;</li>
            <li>directions for further research.</li>
          </ul>
          <p class="mb-2"><strong>CONCLUSION</strong> (not included in the IMRAD format but considered a mandatory section)</p>
          <p class="mb-3">The section should include:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>final generalizations;</li>
            <li>theoretical conclusions;</li>
            <li>recommendations based on the review findings.</li>
          </ul>
          <p class="mb-0">Citations should not be included in this section.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Figures, Formulas, and Tables</h4>
          <p class="mb-4">Figures should be prepared using CorelDRAW or one of the Microsoft Office applications. Graphs, figures, and photographs should be placed in the manuscript immediately after their first mention in the text. In the electronic version of the manuscript, each figure, photograph, graph, and other illustrative material should additionally be submitted to the editorial board as a separate file. Illustrations, tables, and formulas may be formatted across the full width of the page. The caption of an illustration should be centered below it. After the word "Figure" (12 pt, bold font), the sequential number of the figure should be indicated, followed by the figure title in 12 pt regular font. If the manuscript contains only one figure, it should not be numbered.</p>
          <p class="mb-4">Formulas should be prepared using Microsoft Equation or MathType. Formulas should be centred on the page, while their sequential number should be indicated in parentheses and aligned to the right margin. If the manuscript contains only one formula, it should not be numbered.</p>
          <p class="mb-0">The word "Table" with its sequential number should be placed above the table and aligned to the right. On the following line, the title of the table should be provided, centered, without paragraph indentation or line breaks. No full stop should be placed at the end of the table title. One line space should be left after the table. If the manuscript contains only one table, it should not be numbered.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">References and Citations</h4>
          <p class="mb-4">In-text references should be provided in square brackets and include the author's surname, year of publication, and page number: [Ivanov, 1990: 25]; for two authors – [Toshmatov &amp; Azizova, 2023: 45]; for three or more authors – [Toshmatov et al., 2025: 56].</p>
          <p class="mb-4">The manuscript should include no fewer than 30 and no more than 60 references. Every source included in the reference list must be cited in the main text through a corresponding in-text reference. The number of sources must be identical in both versions of the reference list.</p>
          <p class="mb-4">In-text references to sources in foreign languages should be provided in the language of the article's publication. The reference list should also be presented in the original language of the cited sources.</p>
          <p class="mb-4">The author bears full responsibility for the accuracy of quotations and the correct formatting of references.</p>
          <p class="mb-4">Examples included in the manuscript should be italicised and presented without quotation marks. The source of the example, including the author's surname, initials, and page number, should be indicated in parentheses: <em>She had not known the weight until she felt the freedom</em> (Morrison T. Beloved, 112).</p>
          <p class="mb-4">In manuscripts written in English, examples in Russian should be presented in the original language and accompanied by a literal (interlinear) English translation.</p>
          <p class="mb-4">The reference list should be placed after the main text of the article in alphabetical order under the headings FOYDALANILGAN ADABIYOTLAR / LITERATURA and REFERENCES. No full stop or colon should be placed after the headings. The headings should be formatted in 14 pt bold font. The reference list must be prepared in accordance with APA style. References to the author's own publications should not exceed one-third of the total number of sources.</p>
          <p class="mb-4">Sources published in Russian should be transliterated automatically using the BGN (Board of Geographic Names) system available at translit.ru.</p>
          <p class="mb-2"><strong>LITERATURA</strong></p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>1. Abramyan, L., Barker, A., Belkov, P. (2004). Sovremennyye tendentsii v antropologicheskikh issledovaniyakh. <em>Antropologicheskiy forum</em>, 1, 6–101.</li>
            <li>2. Agapkin, I.I. (2018). Ideya «kosmo-psikho-logosa» v tvorcheskom nasledii G.D. Gacheva. <em>Vestnik Russkoy khristianskoy gumanitarnoy akademii</em>, 19(2), 261–268.</li>
            <li>3. Baryshnikov, P.N. (2010). <em>Mif i metafora: lingvofilosofskiy podkhod</em>. Sankt-Peterburg: Aleteyya.</li>
            <li>4. Gumbol'dt, fon V. (2000). <em>Izbrannyye trudy po yazykoznaniyu</em> (2-ye izd.). Moskva: Progress.</li>
          </ul>
          <p class="mb-3">If the manuscript is not written in English, the reference list should be provided in two versions:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>The first version should be presented entirely in Latin script. Sources published in Russian should be provided in Latin transliteration.</li>
            <li>The second version should be provided entirely in English. For sources originally published in languages other than English, the language of publication should be indicated in parentheses at the end of the reference, for example: (in Russian), (in Uzbek), etc.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">III. Article Review Procedure</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>1. Upon submission, the article initially undergoes a technical screening, followed by plagiarism detection. After compliance with the journal requirements has been confirmed, the manuscript is forwarded for peer review. The identities of reviewers are not disclosed to the authors and reviewers are likewise not provided with information about the authors.</li>
            <li>2. The editorial board does not publish manuscripts on a commercial or commissioned basis and does not guarantee publication within timeframes specified by the authors. The editorial board reserves the right to make necessary editorial corrections and reductions to the manuscript.</li>
            <li>3. If a manuscript is returned to the author for revision, the revised version must be resubmitted for repeated review. If additional revisions are required following the repeated review, the revision process continues until a positive review decision is obtained.</li>
            <li>4. Manuscripts returned for revision are considered newly submitted and are reviewed for the issue during which they were resubmitted. Manuscripts in which plagiarism is detected are returned to the author for correction and subsequently undergo repeated plagiarism screening. Editorial cooperation with the author continues until the manuscript achieves an originality level of at least 80%.</li>
            <li>5. Following a positive review decision, the editorial board determines whether the manuscript may be accepted for publication in the journal.</li>
            <li>6. ATTENTION! All communication between the editorial board, the journal expert, and the authors is conducted via email throughout all stages of manuscript processing. Authors are required to provide a valid email address and promptly notify the editorial board of any changes. In the case of co-authored manuscripts, correspondence is conducted with the designated corresponding author.</li>
            <li>7. The editorial board does not consider appeals concerning editorial decisions, reviewers' comments, or other matters related to manuscript submission, formatting, peer review, and publication procedures. Editorial decisions regarding manuscripts are made collectively by the editorial board.</li>
            <li>8. Manuscripts that have undergone the review process are not returned to the authors.</li>
            <li>9. The author(s) bear full responsibility for scientific and factual accuracy, as well as for the quality of the abstract translation. In such cases, the revised manuscript must be resubmitted together with the necessary corrections and justified explanations.</li>
            <li>10. No substantial changes may be introduced after the manuscript has been typeset. Authors have the right to withdraw the manuscript from publication; however, payment for the review process remains mandatory.</li>
            <li>11. The scientific views expressed by the author may not necessarily coincide with the position of the editorial board.</li>
            <li>12. The editorial board kindly requests that authors observe the principles of academic ethics in scholarly communication, refrain from unfounded evaluative judgments, and avoid inappropriate statements regarding the journal regulations and expert reviews.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">IV. Journal Policy</h4>
          <p class="mb-2"><strong>Policy on the Use of Artificial Intelligence in Manuscript Preparation</strong></p>
          <p class="mb-4">The author(s) are required to disclose any use of artificial intelligence in the preparation of the manuscript. Artificial intelligence tools cannot be identified as authors of the manuscript, and full responsibility for the content of the manuscript rests solely with the author(s).</p>
          <p class="mb-4">The use of artificial intelligence is permitted solely for language editing, translation, and stylistic improvement of the text. The use of artificial intelligence for generating scientific results, analytical conclusions, unreliable information, or fictitious references is strictly prohibited.</p>
          <p class="mb-4">ATTENTION! Every manuscript submitted to the journal must include one of the following statements. For example:</p>
          <p class="mb-4"><em>"Artificial intelligence tools were used exclusively for language editing and stylistic improvement during the preparation of this manuscript. The scientific content, analysis, and conclusions are the sole responsibility of the author."</em></p>
          <p class="mb-3">If artificial intelligence has not been used:</p>
          <p class="mb-0"><em>"No artificial intelligence tools were used in the preparation of this manuscript."</em></p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">V. Copyright</h4>
          <p class="mb-4">By submitting a manuscript to the editorial board, the authors consent to its publication in the journal Philology Matters in electronic form without payment of an honorarium. Upon publication, the authors transfer copyright for the published manuscript to the Uzbekistan State World Languages University. Authors of manuscripts accepted for publication are required to conclude a copyright agreement. The full text of the agreement is available in the "For Authors" section of the journal website.</p>
          <p class="mb-0">Authors retain the right to use their materials in subsequent publications, provided that proper reference to the original publication in Philology Matters is indicated. Furthermore, in accordance with the Law of the Republic of Uzbekistan "On Personal Data" No. LRU-547 dated July 2, 2019, authors submitting manuscripts for publication consent to Uzbekistan State World Languages University processing the personal data provided, including its collection, systematization, storage, updating, use, and destruction. Such consent must be confirmed by the personal scanned signature of the author(s) and submitted together with the manuscript materials. This consent is granted for an indefinite period and may be withdrawn by written notification.</p>
        </section>
        ''',
        'content_uz': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">I. Maqolani nashrga tayyorlab yuborish</h4>
          <p class="mb-4">Maqola jurnalning rasmiy veb-sayti orqali yuboriladi: <a href="https://philmatt.uzswlu.uz/" class="text-fmmain hover:underline">https://philmatt.uzswlu.uz/</a>. Maqola ekspertga elektron shaklda ikki variantda taqdim etiladi. Har bir variant alohida fayl ko'rinishida yuboriladi; maqolaning birinchi varianti uchun fayl nomi: <strong>Familiya_maqola.docx</strong>; maqolaning ikkinchi varianti uchun (unda muallifning shaxsiy ma'lumotlari olib tashlanadi) fayl nomi: <strong>Maqola.docx</strong>.</p>
          <p class="mb-4">Birinchi variant ko'rsatilgan talablarga muvofiq rasmiylashtiriladi. Ikkinchi variantda muallif(lar) haqidagi barcha ma'lumotlar (ism-familiyasi, tashkilot nomi, elektron pochta manzili, shuningdek qo'lyozma yuborilgan tashkilot nomi) olib tashlanadi. Muallifning o'z ishlariga berilgan havolalarda F.I.Sh. o'rniga "muallif" so'zi qo'llaniladi.</p>
          <p class="mb-4">Taqdim etilayotgan maqola avval boshqa nashrlarda chop etilmagan bo'lishi shart. Maqola muallif (mualliflar) tomonidan mustaqil bajarilgan original tadqiqot natijalarini o'z ichiga olishi va uning ilmiy yangiligi, dolzarbligi, nazariy va amaliy ahamiyati bilan aniq tavsiflanishi lozim.</p>
          <p class="mb-4">Jurnal talablariga texnik jihatdan mos kelgan maqola qo'lyozmalari antiplag.uz yoki turnitin.com dasturida tekshiriladi. Maqolaning originallik darajasi 80%dan yuqori bo'lsa, tahrirlash bosqichiga o'tkaziladi.</p>
          <p class="mb-4">Tahrirlash − double blind peer review (ikki tomonlama yopiq taqriz) asosida amalga oshiriladi. Taqrizchilarning ijobiy xulosasini olgan maqola keyingi bosqichga tayyorlash uchun ekspertga yuboriladi.</p>
          <p class="mb-0">Maqolani jurnal talablariga mos keltirish maqsadida jurnal eksperti muallifga yordam beradi. Jurnal tahririyati doim maqolaning nashr etilishiga yo'naltirilgan bo'lib, qo'lyozma ijobiy baholangunga qadar muallif bilan konstruktiv hamkorlik qiladi. Muallif bilan muharrir faoliyati ekspert orqali amalga oshadi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">II. Maqolaning texnik jihatdan rasmiylashtirilishi</h4>
          <p class="mb-4">Maqola matnining hajmi 4000–7000 ta so'zdan (doktorantlar, mustaqil izlanuvchilar va professor-o'qituvchilar uchun) hamda 2500–3000 ta so'zdan (magistrantlar uchun) tashkil topishi va DOCX formatida 1,5 intervalda, Times New Roman shriftida, barcha tomondan 2 sm qoldirib yozilgan sahifalarda taqdim etilishi zarur.</p>
          <p class="mb-4">Yuqori qatorda markaz bo'ylab maqola nomi – sarlavha 14 pt hajmda QALIN BOSMA BOSH HARFLAR bilan, markazda, abzats chekinishisiz beriladi. Sarlavha oxirida nuqta qo'yilmaydi. Maqola nomi uch tilda: o'zbek, ingliz va rus tillarida (hamda maqola tilida) taqdim etiladi.</p>
          <p class="mb-4">Maqola sarlavhasidan keyin muallif(lar)ning ismi, otasining ismi va familiyasi (uch tilda: o'zbek, ingliz va rus tillarida (hamda maqola tilida)) – 14 pt, qalin shrift bilan yoziladi. Bir maqolada 3 tadan ortiq muallif bo'lmasligi kerak!</p>
          <p class="mb-4">Keyingi qatorda muallif(lar)ning ish joyi hisoblangan tashkilotning to'liq nomi, shahar va mamlakat ko'rsatiladi, undan keyingi qatorda korrespondent muallifning elektron pochta manzili beriladi (14 pt) (uch tilda: o'zbek, ingliz va rus tillarida (hamda maqola tilida)). Agar mualliflar turli tashkilotlarda ishlasa, har bir muallif uchun alohida tashkilot nomi (affiliatsiya) ko'rsatiladi. Faqat muallif(lar)ning asosiy ish yoki ta'lim maskani ko'rsatiladi. Shundan so'ng muallif(lar)ning ORCID ID(lar)i keltiriladi. Muallif(lar) haqidagi ma'lumotlar har bir tilda alohida-alohida taqdim etilishi kerak.</p>
          <p class="mb-4">Keyingi qatorda maqolaning annotatsiyasi beriladi. Unda mavzuning tavsifi, maqsad, vazifalar, metodlar, asosiy natijalar va xulosalar qamrab olinadi; hajmi – 250–300 ta so'z (doktorantlar, mustaqil izlanuvchilar va professor-o'qituvchilar uchun) hamda 150–200 ta so'z (magistrantlar uchun) (uch tilda: o'zbek, ingliz va rus tillarida (hamda maqola tilida)), 14 pt qalin, abzatsning chap va o'ng tomonlaridan 2 sm chekinish, kenglik bo'yicha tekislash, birinchi qator chekinishi – 1 sm. Annotatsiyadan keyin – 1,5 interval tashlanadi.</p>
          <p class="mb-4">Annotatsiya ostida 8–10 ta kalit so'z (doktorantlar, mustaqil izlanuvchilar va professor-o'qituvchilar uchun) hamda 6–8 ta kalit so'z (magistrantlar uchun) yoki tushunchalar (ish mavzusini aks ettiruvchi va tegishli ma'lumotni izlashda kalit vazifasini bajaruvchi) beriladi, 14 pt, abzatsning chap va o'ng tomonlaridan 2 sm chekinish, kenglik bo'yicha tekislash (Kalit so'zlar: so'zlar, so'zlar va h.k.). Kalit so'zlardan keyin – 1,5 interval tashlanadi.</p>
          <p class="mb-0">Matn 14 pt oddiy shrift bilan yoziladi. Abzats kenglik bo'yicha tekislanadi, birinchi qator chekinishi – 1 sm. Jurnalda ikki turdagi maqolalar chop etiladi va ular IMRAD strukturasi asosida rasmiylashtirilishi lozim.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">1. Original Research Article (IMRAD strukturasi)</h4>
          <p class="mb-4"><strong>Original Research Article</strong> (original ilmiy maqola) — muallif tomonidan ilk bor o'tkazilgan empirik tadqiqot natijalariga asoslangan maqola. Ya'ni muallif ma'lumotlarni mustaqil yig'adi, tahlil qiladi va xulosa chiqaradi. U quyidagi bo'limlar va strukturadan iborat bo'lishi kerak (IMRAD tarkibiy bo'limlari nomlari TO'LIQ BOSH HARFLARDA yoziladi):</p>
          <p class="mb-2"><strong>INTRODUCTION (KIRISH)</strong></p>
          <p class="mb-3">Mazkur bo'lim ilmiy muammoni asoslaydi. Unda quyidagi jihatlar aks etishi lozim:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>tadqiqot mavzusining dolzarbligi;</li>
            <li>ilmiy muammoning qo'yilishi;</li>
            <li>mavjud tadqiqotlar bo'yicha qisqa sharh;</li>
            <li>ilmiy bo'shliqni aniqlash (research gap);</li>
            <li>tadqiqotning maqsadi va vazifalari;</li>
            <li>gipoteza (mavjud bo'lsa).</li>
          </ul>
          <p class="mb-4"><em>→ Natija: mazkur tadqiqot zarurligini asoslash.</em></p>
          <p class="mb-2"><strong>METHODS (TADQIQOT METODLARI)</strong></p>
          <p class="mb-3">Tadqiqotning takrorlanuvchanligini ta'minlovchi asosiy bo'lim. Unda quyidagilar yoritilishi lozim:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>tadqiqot dizayni (eksperimental, korrelyatsion, korpus tahlili va boshq.);</li>
            <li>tadqiqot obyekti va predmeti;</li>
            <li>ma'lumot yig'ish metodlari: so'rovnoma; intervyu; kuzatish; matn/korpus tahlili;</li>
            <li>tanlanma tavsifi: hajmi; parametrlari;</li>
            <li>tahlil metodlari: statistik (SPSS, R va boshqalar); lingvistik/kognitiv;</li>
            <li>ishonchlilik va validlik masalalari.</li>
          </ul>
          <p class="mb-4"><em>→ Natija: tadqiqotni to'liq qayta takrorlash imkoniyati.</em></p>
          <p class="mb-2"><strong>RESULTS (NATIJALAR)</strong></p>
          <p class="mb-3">Bu yerda faqat faktik ma'lumotlar interpretatsiyasiz taqdim etiladi. Quyidagilar yoritilishi lozim:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>asosiy empirik natijalar;</li>
            <li>jadval, grafik va diagrammalar (mavjud bo'lsa);</li>
            <li>statistik ko'rsatkichlar;</li>
            <li>aniqlangan qonuniyatlar.</li>
          </ul>
          <p class="mb-4"><em>→ Muhim: faqat "nima natija olindi?" savoliga javob.</em></p>
          <p class="mb-2"><strong>DISCUSSION (MUNOZARA)</strong></p>
          <p class="mb-3">Olingan natijalarni talqin qilish. Quyidagilar yoritilishi lozim:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>natijalarni izohlash;</li>
            <li>oldingi tadqiqotlar bilan taqqoslash;</li>
            <li>gipotezaning tasdiqlanishi yoki rad etilishi;</li>
            <li>nazariy ahamiyati;</li>
            <li>amaliy ahamiyati;</li>
            <li>tadqiqot cheklovlari;</li>
            <li>keyingi tadqiqot istiqbollari.</li>
          </ul>
          <p class="mb-4"><em>→ Bu yerda ishning ilmiy qiymati ochib beriladi.</em></p>
          <p class="mb-2"><strong>CONCLUSION (XULOSA)</strong> (IMRAD tarkibiga kirmaydi, lekin majburiy)</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>yakuniy xulosalar;</li>
            <li>ilmiy yangilik;</li>
            <li>qisqa umumlashtirish;</li>
            <li>iqtiboslarsiz.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">2. Review Article (IMRAD strukturasi)</h4>
          <p class="mb-4"><strong>Review Article</strong> (sharh ilmiy maqola yoki tahliliy maqola) — muayyan ilmiy yo'nalish bo'yicha avval chop etilgan tadqiqotlarni tizimli tahlil qilish, taqqoslash va umumlashtirishni o'z ichiga olgan maqola. Ya'ni, muallif yangi empirik ma'lumotlar yig'maydi, balki mavjud ilmiy ishlar asosida nazariy va metodologik xulosalar chiqaradi. U quyidagi bo'limlar va strukturadan iborat bo'lishi kerak (IMRAD tarkibiy bo'limlari nomlari TO'LIQ BOSH HARFLARDA yoziladi):</p>
          <p class="mb-2"><strong>INTRODUCTION (KIRISH)</strong></p>
          <p class="mb-3">Unda quyidagilar yoritilishi lozim:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>ilmiy yo'nalishning dolzarbligi;</li>
            <li>sharh zarurligini asoslash;</li>
            <li>muammoning qo'yilishi;</li>
            <li>sharhning maqsadi.</li>
          </ul>
          <p class="mb-4"><em>→ Ilmiy bo'shliqni ko'rsatish majburiy.</em></p>
          <p class="mb-2"><strong>METHODS (TADQIQOT METODLARI)</strong></p>
          <p class="mb-3">Ko'pincha e'tibordan chetda qoladi, lekin majburiy hisoblanadi. Unda quyidagilar yoritilishi lozim:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>manbalarni tanlash mezonlari: vaqt oralig'i; ma'lumotlar bazalari (Scopus, Web of Science va boshqalar);</li>
            <li>qidiruv strategiyasi (kalit so'zlar);</li>
            <li>kiritish/chiqarib tashlash mezonlari;</li>
            <li>tahlil metodlari: tematik tahlil; meta-tahlil (mavjud bo'lsa).</li>
          </ul>
          <p class="mb-4"><em>→ Sharhning ilmiy asoslanganligini ta'minlaydi.</em></p>
          <p class="mb-2"><strong>RESULTS (NATIJALAR)</strong></p>
          <p class="mb-3">Bu yerda empirik ma'lumotlar emas, balki adabiyotlar tahlili natijalari taqdim etiladi. Quyidagilar yoritilishi lozim:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>asosiy ilmiy yondashuvlar;</li>
            <li>nazariy maktablar;</li>
            <li>tadqiqotlardagi qarama-qarshiliklar;</li>
            <li>zamonaviy tendensiyalar;</li>
            <li>taqqoslovchi jadvallar.</li>
          </ul>
          <p class="mb-4"><em>→ Mavzu bo'yicha "ilmiy manzara" shakllantiriladi.</em></p>
          <p class="mb-2"><strong>DISCUSSION (MUNOZARA)</strong></p>
          <p class="mb-3">Asosiy analitik bo'lim. Unda quyidagilar yoritilishi lozim:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>adabiyotlar asosida umumlashtirilgan xulosalar;</li>
            <li>mavjud yondashuvlarni baholash;</li>
            <li>ilmiy bo'shliqlarni aniqlash;</li>
            <li>muammoli jihatlar;</li>
            <li>keyingi tadqiqot istiqbollari.</li>
          </ul>
          <p class="mb-2"><strong>CONCLUSION (XULOSA)</strong> (IMRAD tarkibiga kirmaydi, lekin majburiy)</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>yakuniy umumlashtirishlar;</li>
            <li>nazariy xulosalar;</li>
            <li>tavsiyalar;</li>
            <li>iqtiboslarsiz.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Rasmlar, formulalar va jadvallar</h4>
          <p class="mb-4">Rasmlar Corel Draw grafik muharririda yoki MS Office dasturlaridan birida tayyorlangan holatda bajariladi. Grafiklar, rasmlar va fotosuratlar matnga ular birinchi marta tilga olingandan keyin joylashtiriladi. Taqdim etiladigan elektron variantda har bir rasm, fotosurat, grafik va boshqalar tahririyatga alohida fayl ko'rinishida ham topshirilishi lozim. Illyustratsiyalar, jadvallar va formulalarni sahifa kengligi bo'ylab joylashtirishga ruxsat etiladi. Illyustratsiya nomi (12 pt, oddiy) ularning ostida markaz bo'yicha, tartib raqami bilan "Rasm" so'zidan keyin (12 pt, qalin) beriladi. Agar matnda bitta rasm bo'lsa, raqam qo'yilmaydi.</p>
          <p class="mb-4">Formulalar MS Equation yoki Math Type formulalar muharriri yordamida yoziladi. Formula markazga joylashtiriladi, uning tartib raqami dumaloq qavs ichida o'ng tomonda beriladi (o'ng tomon bo'yicha tekislash qo'llaniladi). Agar maqolada bitta formula bo'lsa, u raqamlanmaydi.</p>
          <p class="mb-0">"Jadval" so'zi tartib raqami bilan jadvaldan oldin o'ng tomonda joylashtiriladi. Keyingi qatorda jadval nomi beriladi (markaz bo'yicha, abzatssiz va bo'g'inlarga ajratilmasdan), oxirida nuqta qo'yilmaydi. Jadvaldan keyin 1 interval qoldiriladi. Agar maqolada bitta jadval bo'lsa, u raqamlanmaydi.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Havolalar va adabiyotlar ro'yxati</h4>
          <p class="mb-4">Matn ichida manbalarga havolalar muallif familiyasi, nashr yili va iqtibos keltirilgan sahifa ko'rsatilgan holda kvadrat qavs ichida beriladi [Ivanov, 1990: 25], ikki muallif bo'lsa [Toshmatov &amp; Azizova, 2023: 45], uch va undan ortiq muallif bo'lsa [Toshmatov va boshq., 2025: 56].</p>
          <p class="mb-4">Maqolada kamida 30 ta, ko'pi bilan 60 ta manbadan foydalanish lozim. Shu bilan birga, keltirilgan har bir manbaga maqola matnida belgilangan tartibda albatta havola berilishi shart. Adabiyotlar ro'yxatining har ikki variantida ham manbalar soni bir xil bo'lishi kerak.</p>
          <p class="mb-4">Muallif maqolada keltirilgan iqtiboslarning aniqligi va manbalarga havolalarni to'g'ri rasmiylashtirilishi uchun javobgar hisoblanadi.</p>
          <p class="mb-4">Maqola matnidagi misollar kursivda, qo'shtirnoqsiz beriladi. Misol manbalari nomlari, muallif familiyalari (initsiallari bilan) dumaloq qavs ichida beriladi, sahifalar ko'rsatiladi: <em>Shu orada hujraga bir chol kirib ul ham mehmonlar bilan so'rashib chiqdi</em> (Qodiriy A. "O'tkan kunlar", 73).</p>
          <p class="mb-4">Adabiyotlar ro'yxati maqola matnidan keyin alifbo tartibida FOYDALANILGAN ADABIYOTLAR / LITERATURA va REFERENCES so'zlaridan so'ng beriladi (oxirida nuqta yoki ikki nuqta qo'yilmaydi). Shrift – 14 pt, qalin. Adabiyotlar ro'yxati APA (6th) formatida rasmiylashtiriladi. O'z ishlariga havolalar umumiy manbalar sonining uchdan bir qismidan oshmasligi lozim.</p>
          <p class="mb-4">RUS TILIDAGI MANBALAR BGN (Board of Geographic Names) dasturi yordamida http://www.translit.ru saytida avtomatik transliteratsiya qilinishi va rus tilidagi tavsifdan keyin transliteratsiya qilingan varianti keltirilishi lozim.</p>
          <p class="mb-2"><strong>LITERATURA</strong></p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>1. Abramyan, L., Barker, A., Belkov, P. (2004). Sovremennyye tendentsii v antropologicheskikh issledovaniyakh. <em>Antropologicheskiy forum</em>, 1, 6–101.</li>
            <li>2. Agapkin, I.I. (2018). Ideya «kosmo-psikho-logosa» v tvorcheskom nasledii G.D. Gacheva. <em>Vestnik Russkoy khristianskoy gumanitarnoy akademii</em>, 19(2), 261–268.</li>
            <li>3. Baryshnikov, P.N. (2010). <em>Mif i metafora: lingvofilosofskiy podkhod</em>. Sankt-Peterburg: Aleteyya.</li>
            <li>4. Gumbol'dt, fon V. (2000). <em>Izbrannyye trudy po yazykoznaniyu</em> (2-ye izd.). Moskva: Progress.</li>
          </ul>
          <p class="mb-3">Foydalanilgan adabiyotlar ro'yxati maqola ingliz tilida yozilmagan bo'lsa, ikki variantda keltiriladi:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>birinchi ro'yxat – to'liq lotin yozuvida (bunda rus tilidagi manbalar lotin transliteratsiyasida beriladi);</li>
            <li>ikkinchi ro'yxat – to'liq ingliz tilida beriladi, bunda original tili ingliz tilida bo'lmagan manbalar oxirida ularning asliyat tili qavs ichida ko'rsatiladi, masalan: (in Russian), (in Uzbek) va h.k.z.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">III. Qo'lyozmalarni taqrizdan o'tkazish tartibi</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>1. Kelib tushgan qo'lyozma dastlab texnik tekshiruvdan o'tkaziladi, so'ng antiplagiat tekshiruvi amalga oshiriladi va belgilangan talablarga muvofiqligi aniqlangach, taqrizga yuboriladi. Taqrizchilarning ism-familiyalari qo'lyozma mualliflariga ma'lum qilinmaydi. O'z navbatida, mualliflarga ham taqrizchilarning ism-familiyalari oshkor qilinmaydi.</li>
            <li>2. Tahririyat tijorat asosida buyurtma maqolalarni chop etmaydi va muallif tomonidan ko'rsatilgan nashr muddatlari bo'yicha majburiyat olmaydi. Tahririyat qo'lyozmaga zarur tahririy tuzatishlar va qisqartirishlar kiritish huquqini o'zida saqlab qoladi.</li>
            <li>3. Agar qo'lyozma qayta ishlash uchun muallifga yuborilsa, tegishli o'zgartirishlar kiritilgandan so'ng u qayta taqrizdan o'tkazish uchun yana ekspertga taqdim etiladi. Agar takroriy taqriz natijasida ham maqolani qayta ishlash zarur deb topilsa, jarayon ijobiy natija olinguncha davom ettiriladi.</li>
            <li>4. Tahrir hay'ati tomonidan qayta ishlashga yuborilgan maqolalar yangi kelib tushgan material sifatida ko'rib chiqiladi va ular qayta ko'rib chiqilayotgan paytdagi son uchun qabul qilinadi. Plagiat aniqlangan maqolalar zarur tuzatishlar kiritilishi uchun muallifga qaytariladi hamda qaytadan antiplagiat tekshiruvidan o'tkaziladi. Muallif bilan hamkorlik originallik darajasi kamida 80% ga yetguncha davom ettiriladi.</li>
            <li>5. Ijobiy taqriz olingandan so'ng tahririyat qo'lyozmani jurnalda chop etish imkoniyati yuzasidan qaror qabul qiladi.</li>
            <li>6. DIQQAT! Qo'lyozmalar bilan ishlashning barcha bosqichlarida, shuningdek mualliflar bilan muloqotda ekspert va tahririyat elektron pochtadan foydalanadi. Mualliflar elektron manzilni to'g'ri ko'rsatishlari va uning o'zgarishi haqida o'z vaqtida xabar berishlari shart. Agar maqolaning bir nechta muallifi bo'lsa, yozishmalar ulardan biri – "korrespondent muallif" bilan olib boriladi.</li>
            <li>7. Tahririyat maqola bo'yicha qabul qilingan qarorlar, taqrizchilarning e'tirozlari, shuningdek maqolalarni taqdim etish, rasmiylashtirish, taqrizdan o'tkazish va nashr etish tartibiga oid boshqa masalalar yuzasidan mualliflar bilan munozaraga kirishmaydi. Maqola bo'yicha xulosa tahririyatning jamoaviy qarori hisoblanadi.</li>
            <li>8. Taqrizdan o'tgan qo'lyozmalar qaytarilmaydi.</li>
            <li>9. Ilmiy va faktik xatolar, shuningdek annotatsiya tarjimasining sifati uchun muallif(lar) javobgar hisoblanadi. Bunday holatlarda muallif(lar) zarur tuzatishlar kiritilgan va asosli ma'lumotlar ilova qilingan holda qo'lyozmani qayta ekspertga taqdim etadi.</li>
            <li>10. Maketga jiddiy o'zgartirishlar kiritishga yo'l qo'yilmaydi. Muallif maqolani nashr etishdan voz kechish huquqiga ega, biroq taqriz uchun to'lov majburiy hisoblanadi.</li>
            <li>11. Maqola muallifining ilmiy qarashlari va baholari tahririyat pozitsiyasini aks ettirmasligi mumkin.</li>
            <li>12. Tahririyat mualliflardan ilmiy munozara etikasi qoidalariga rioya qilishni, asossiz baholardan hamda belgilangan qoidalar va ekspert xulosalariga nisbatan noo'rin fikrlar bildirishdan tiyilishni so'raydi.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">IV. Jurnal siyosati</h4>
          <p class="mb-2"><strong>Jurnalning ilmiy-metodik maqolalarni tayyorlashda muallif(lar) tomonidan sun'iy intellekt texnologiyalaridan foydalanish bo'yicha siyosati</strong></p>
          <p class="mb-4">Muallif(lar) maqola tayyorlash jarayonida sun'iy intellekt texnologiyalaridan foydalanish holatlarini ochiq ko'rsatishlari shart. Sun'iy intellekt vositalari muallif sifatida tan olinmaydi va maqola mazmuni uchun to'liq javobgarlik muallif(lar) zimmasida bo'ladi.</p>
          <p class="mb-4">Sun'iy intellektdan tilni tahrirlash, tarjima va stilistik yaxshilash maqsadida foydalanishga ruxsat etiladi. Sun'iy intellekt yordamida ilmiy natijalar va tahliliy xulosalarni yaratish, shuningdek ishonchsiz ma'lumotlar va soxta manbalarni keltirish qat'iyan man etiladi.</p>
          <p class="mb-4">DIQQAT! Jurnalga taqdim etiladigan maqola(lar)da quyidagi bayonot albatta bo'lishi kerak. Masalan:</p>
          <p class="mb-4"><em>"Mazkur maqolani tayyorlashda sun'iy intellekt vositalaridan faqat tilni tahrirlash va stilistik yaxshilash maqsadida foydalanildi. Ilmiy mazmun, tahlil va xulosalar muallifga tegishli".</em></p>
          <p class="mb-3">Agar sun'iy intellektdan foydalanilmagan bo'lsa:</p>
          <p class="mb-0"><em>"Muallif ushbu maqolani tayyorlashda sun'iy intellekt vositalaridan foydalanmadi".</em></p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">V. Mualliflik huquqlari</h4>
          <p class="mb-4">Qo'lyozmalarni tahririyatga taqdim etishda mualliflar "Filologiya masalalari" jurnalida elektron va/yoki bosma shaklda gonorarsiz chop etilishiga rozilik bildiradilar. Mazkur jurnalda nashr etilgan taqdirda mualliflar o'z maqolalariga bo'lgan mualliflik huquqlarini O'zbekiston davlat jahon tillari universitetiga topshiradilar. Nashrga qabul qilingan maqolalar mualliflari mualliflik shartnomasini tuzadilar. Shartnomaning to'liq matni jurnal saytining "Mualliflar uchun" bo'limida mavjud.</p>
          <p class="mb-0">Mualliflar o'z materiallaridan keyingi nashrlarida foydalanish huquqiga ega va bunda "Filologiya masalalari" jurnalida chop etilganiga havola berilishi lozim. Bundan tashqari, O'zbekiston Respublikasining 2019-yil 2-iyuldagi "Shaxsga doir ma'lumotlar to'g'risida"gi O'RQ-547-son Qonuniga muvofiq, o'z maqolalarini chop etayotgan mualliflar O'zbekiston davlat jahon tillari universitetiga taqdim etilgan shaxsiy ma'lumotlarini qayta ishlashga rozilik bildiradilar, jumladan, ularni yig'ish, tizimlashtirish, jamlash, saqlash, aniqlashtirish (yangilash, o'zgartirish), foydalanish va yo'q qilish. Mazkur rozilik muallif(lar)ning shaxsiy skanerlangan imzosi bilan tasdiqlanadi va nashr uchun yuborilayotgan materiallar bilan birga taqdim etiladi. Ushbu rozilik muallif(lar) tomonidan noma'lum muddatga beriladi va yozma ravishda xabarnoma yuborish orqali bekor qilinishi mumkin.</p>
        </section>
        ''',
        'content_ru': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">I. Подготовка статьи к публикации</h4>
          <p class="mb-4">Статья отправляется через официальный веб-сайт журнала: <a href="https://philmatt.uzswlu.uz/" class="text-fmmain hover:underline">https://philmatt.uzswlu.uz/</a>. Каждый вариант направляется отдельным файлом. Первый вариант статьи со сведениями об авторе (авторах) – фамилия, имя, организация, адрес электронной почты, должен быть сохранён под фамилией автора: <strong>Фамилия_статья.docx</strong>; второй вариант статьи (без сведений об авторе): <strong>Статья.docx</strong>. Во втором варианте в ссылках на собственные работы автора вместо фамилии, имени и отчества используется слово «автор».</p>
          <p class="mb-4">Представляемая статья не должна быть ранее опубликована в других изданиях и должна содержать результаты оригинального исследования автора, с отражением её научной новизны, актуальности, теоретической и практической значимости работы.</p>
          <p class="mb-4">Статьи, прошедшие техническую экспертизу, проверяются в программах antiplag.uz или turnitin.com. К редакционной обработке допускаются материалы с уровнем оригинальности выше 80%.</p>
          <p class="mb-4">Редактирование статьи осуществляется на основе double blind peer review (двустороннего слепого рецензирования). Статья, получившая положительное заключение рецензентов, направляется эксперту для подготовки к следующему этапу.</p>
          <p class="mb-0">В целях приведения статьи в соответствие с требованиями журнала автору оказывается содействие со стороны эксперта журнала. Редакция журнала ориентирована на публикацию статьи и осуществляет конструктивное сотрудничество с автором до получения положительного заключения. Взаимодействие автора и редактора осуществляется через эксперта.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">II. Техническое оформление статьи</h4>
          <p class="mb-4">Объём статьи должен составлять 4000–7000 слов (для докторантов, самостоятельных соискателей и профессорско-преподавательского состава) и 2500–3000 слов (для магистрантов). Статья представляется в формате DOCX, оформляется шрифтом Times New Roman с межстрочным интервалом 1,5 и полями по 2 см со всех сторон.</p>
          <p class="mb-4">В верхней части страницы по центру размещается название статьи – заголовок, набранный ПРОПИСНЫМИ ПОЛУЖИРНЫМИ БУКВАМИ размером 14 pt, без абзацного отступа. Точка в конце заголовка не ставится. Название статьи приводится на узбекском, английском и русском языках (а также на языке статьи).</p>
          <p class="mb-4">После названия статьи указываются имя, отчество и фамилия автора (авторов) на узбекском, английском и русском языках (а также на языке статьи) полужирным шрифтом размером 14 pt. Количество авторов одной статьи не должно превышать трёх.</p>
          <p class="mb-4">На следующей строке указываются полное наименование места работы автора (авторов), город и страна, а на строке ниже – адрес электронной почты корреспондирующего автора (14 pt) (информация предоставляется на узбекском, английском и русском языках (а также на языке статьи)). Если авторы работают в разных организациях, для каждого автора отдельно указывается соответствующая аффилиация. Указывается только основное место работы или учёбы автора (авторов). После этого приводится ORCID ID автора (авторов). Сведения об авторе (авторах) на каждом языке представляются отдельно.</p>
          <p class="mb-4">На следующей строке размещается аннотация статьи. В аннотации должны быть представлены актуальность исследования, цель и задачи работы, методы исследования, основные результаты и выводы. Объём аннотации составляет 250–300 слов для докторантов, самостоятельных исследователей и профессорско-преподавательского состава и 150–200 слов для магистрантов на узбекском, английском и русском языках (а также на языке статьи). Аннотация оформляется полужирным шрифтом размером 14 pt, с отступами по 2 см слева и справа, выравниванием по ширине и абзацным отступом первой строки 1 см. После аннотации оставляется межстрочный интервал 1,5.</p>
          <p class="mb-4">Под аннотацией приводятся 8–10 ключевых слов для докторантов, самостоятельных исследователей и профессорско-преподавательского состава и 6–8 ключевых слов для магистрантов либо понятий, отражающих тему исследования и выполняющих функцию поиска соответствующей информации. Ключевые слова оформляются шрифтом размером 14 pt, с отступами по 2 см слева и справа и выравниванием по ширине. После ключевых слов оставляется межстрочный интервал 1,5.</p>
          <p class="mb-0">Основной текст статьи оформляется обычным шрифтом размером 14 pt. Текст выравнивается по ширине, абзацный отступ первой строки составляет 1 см. В журнале публикуются статьи двух типов, которые должны быть оформлены в соответствии со структурой IMRAD.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">1. Original Research Article (структура IMRAD)</h4>
          <p class="mb-4"><strong>Original Research Article</strong> (оригинальная научная статья) – статья, основанная на результатах эмпирического исследования, впервые проведённого автором. Иными словами, автор самостоятельно осуществляет сбор данных, их анализ и формулирует выводы. Статья должна включать следующие разделы и быть оформлена в соответствии со следующей структурой (названия структурных разделов IMRAD указываются ПРОПИСНЫМИ БУКВАМИ):</p>
          <p class="mb-2"><strong>INTRODUCTION (ВВЕДЕНИЕ)</strong></p>
          <p class="mb-3">Данный раздел посвящён обоснованию научной проблемы. В нём должны быть отражены:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>актуальность темы исследования;</li>
            <li>постановка научной проблемы;</li>
            <li>краткий обзор существующих исследований;</li>
            <li>выявление научного пробела (research gap);</li>
            <li>цель и задачи исследования;</li>
            <li>гипотеза (при наличии).</li>
          </ul>
          <p class="mb-4"><em>→ Результат: обоснование необходимости проведения данного исследования.</em></p>
          <p class="mb-2"><strong>METHODS (МЕТОДЫ)</strong></p>
          <p class="mb-3">Основной раздел, в котором подробно описывается процесс проведения исследования. В данном разделе должны быть отражены:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>дизайн исследования (экспериментальный, корреляционный, корпусный анализ и др.);</li>
            <li>объект и предмет исследования;</li>
            <li>методы сбора данных: анкетирование; интервью; наблюдение; анализ текста / корпуса;</li>
            <li>характеристика выборки: объём; параметры;</li>
            <li>методы анализа: статистические (SPSS, R и др.); лингвистические / когнитивные;</li>
            <li>вопросы надёжности и валидности исследования.</li>
          </ul>
          <p class="mb-4"><em>→ Результат: возможность полного повторного проведения исследования.</em></p>
          <p class="mb-2"><strong>RESULTS (РЕЗУЛЬТАТЫ)</strong></p>
          <p class="mb-3">В данном разделе представляются только фактические данные без их интерпретации. В разделе должны быть отражены:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>основные эмпирические результаты;</li>
            <li>таблицы, графики и диаграммы (при наличии);</li>
            <li>статистические показатели;</li>
            <li>выявленные закономерности.</li>
          </ul>
          <p class="mb-4"><em>→ Важно: данный раздел должен отвечать только на вопрос «Какие результаты были получены?».</em></p>
          <p class="mb-2"><strong>DISCUSSION (ОБСУЖДЕНИЕ)</strong></p>
          <p class="mb-3">В данном разделе осуществляется интерпретация полученных результатов. В разделе должны быть отражены:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>интерпретация результатов;</li>
            <li>сопоставление с предыдущими исследованиями;</li>
            <li>подтверждение или опровержение гипотезы;</li>
            <li>теоретическая значимость;</li>
            <li>практическая значимость;</li>
            <li>ограничения исследования;</li>
            <li>перспективы дальнейших исследований.</li>
          </ul>
          <p class="mb-4"><em>→ В данном разделе раскрывается научная значимость исследования.</em></p>
          <p class="mb-2"><strong>CONCLUSION (ВЫВОДЫ)</strong> (не входит в структуру IMRAD, но является обязательным разделом)</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>итоговые выводы;</li>
            <li>научная новизна исследования;</li>
            <li>краткое обобщение результатов;</li>
            <li>без цитирования.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">2. Review Article (структура IMRAD)</h4>
          <p class="mb-4"><strong>Review Article</strong> (обзорная научная статья или аналитическая статья) – статья, включающая системный анализ, сопоставление и обобщение ранее опубликованных исследований по определённому научному направлению. Иными словами, автор не собирает новые эмпирические данные, а формулирует теоретические и методологические выводы на основе существующих научных работ. Статья должна включать следующие разделы и быть оформлена в соответствии со следующей структурой (названия структурных разделов IMRAD указываются ПРОПИСНЫМИ БУКВАМИ):</p>
          <p class="mb-2"><strong>INTRODUCTION (ВВЕДЕНИЕ)</strong></p>
          <p class="mb-3">В данном разделе должны быть отражены:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>актуальность научного направления;</li>
            <li>обоснование необходимости обзорного исследования;</li>
            <li>постановка проблемы;</li>
            <li>цель обзора.</li>
          </ul>
          <p class="mb-4"><em>→ Обязательным является указание недостаточно изученных аспектов проблемы.</em></p>
          <p class="mb-2"><strong>METHODS (МЕТОДЫ)</strong></p>
          <p class="mb-3">В разделе должны быть отражены:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>критерии отбора источников: временной период; базы данных (Scopus, Web of Science и др.);</li>
            <li>стратегия поиска (ключевые слова);</li>
            <li>критерии включения и исключения источников;</li>
            <li>методы анализа: тематический анализ; метаанализ (при наличии).</li>
          </ul>
          <p class="mb-4"><em>→ Данный раздел обеспечивает научную обоснованность статьи.</em></p>
          <p class="mb-2"><strong>RESULTS (РЕЗУЛЬТАТЫ)</strong></p>
          <p class="mb-3">В данном разделе представляются не эмпирические данные, а результаты анализа научной литературы. В разделе должны быть отражены:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>основные научные подходы;</li>
            <li>теоретические школы;</li>
            <li>противоречия в исследованиях;</li>
            <li>современные тенденции;</li>
            <li>сравнительные таблицы.</li>
          </ul>
          <p class="mb-4"><em>→ В данном разделе формируется целостная научная картина по рассматриваемой теме.</em></p>
          <p class="mb-2"><strong>DISCUSSION (ОБСУЖДЕНИЕ)</strong></p>
          <p class="mb-3">Основной аналитический раздел. В разделе должны быть отражены:</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>обобщённые выводы на основе анализа литературы;</li>
            <li>оценка существующих подходов;</li>
            <li>выявление недостаточно изученных аспектов;</li>
            <li>проблемные вопросы;</li>
            <li>перспективы дальнейших исследований.</li>
          </ul>
          <p class="mb-2"><strong>CONCLUSION (ВЫВОДЫ)</strong> (не входит в структуру IMRAD, но является обязательным разделом)</p>
          <ul class="list-disc list-inside space-y-1 mb-3">
            <li>итоговые обобщения;</li>
            <li>теоретические выводы;</li>
            <li>рекомендации;</li>
            <li>без цитирования.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Рисунки, формулы и таблицы</h4>
          <p class="mb-4">Рисунки выполняются в графическом редакторе Corel Draw или в одной из программ MS Office. Графики, рисунки и фотографии размещаются в тексте после их первого упоминания. В электронной версии статьи каждый рисунок, фотография, график и другие иллюстративные материалы дополнительно представляются в редакцию отдельным файлом. Допускается размещение иллюстраций, таблиц и формул по ширине страницы. Название иллюстрации приводится под ней по центру страницы: после слова «Рисунок» (12 pt, полужирный шрифт) указывается её порядковый номер, затем – название иллюстрации (12 pt, обычный шрифт). Если в статье имеется только один рисунок, он не нумеруется.</p>
          <p class="mb-4">Формулы оформляются с использованием редакторов формул MS Equation или MathType. Формула размещается по центру страницы, её порядковый номер указывается справа в круглых скобках (с выравниванием по правому краю). Если в статье приводится только одна формула, она не нумеруется.</p>
          <p class="mb-0">Слово «Таблица» с порядковым номером размещается над таблицей с выравниванием по правому краю. На следующей строке приводится название таблицы (по центру, без абзацного отступа и без переносов), точка в конце названия не ставится. После таблицы оставляется один интервал. Если в статье имеется только одна таблица, она не нумеруется.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Ссылки и список литературы</h4>
          <p class="mb-4">Внутритекстовые ссылки на источники оформляются в квадратных скобках с указанием фамилии автора, года издания и страницы цитирования: [Ivanov, 1990: 25]; при двух авторах – [Toshmatov &amp; Azizova, 2023: 45]; при трёх и более авторах – [Toshmatov и др., 2025: 56].</p>
          <p class="mb-4">В статье должно быть использовано не менее 30 и не более 60 источников. При этом на каждый источник, включённый в список литературы, в тексте статьи обязательно должна быть дана соответствующая внутритекстовая ссылка. В обоих вариантах списка литературы количество источников должно совпадать.</p>
          <p class="mb-4">Внутритекстовые ссылки на источники на иностранных языках должны приводиться на языке публикации статьи. Список литературы также оформляется на языке оригинального издания источников.</p>
          <p class="mb-4">Автор несёт ответственность за точность приведённых цитат и правильность оформления ссылок на источники.</p>
          <p class="mb-4">Примеры в тексте статьи приводятся курсивом, без кавычек. Источники примеров, фамилии авторов (с инициалами) указываются в круглых скобках с обозначением страниц: <em>На дворе стоял тихий летний вечер, наполненный запахом свежескошенной травы</em> (Тургенев И.С. «Отцы и дети», с. 47). В статье на английском языке примеры на русском языке приводятся в оригинале и сопровождаются дословным (interlinear) переводом на английский язык.</p>
          <p class="mb-4">Список литературы размещается после основного текста статьи в алфавитном порядке после заголовков FOYDALANILGAN ADABIYOTLAR / LITERATURA и REFERENCES (точка или двоеточие в конце заголовков не ставятся). Шрифт 14 pt, полужирный. Список литературы оформляется в формате APA. Ссылки на собственные работы автора не должны превышать одной трети от общего количества источников.</p>
          <p class="mb-4">Источники на русском языке должны быть автоматически транслитерированы с использованием системы BGN (Board of Geographic Names) на сайте translit.ru.</p>
          <p class="mb-2"><strong>LITERATURA</strong></p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>1. Abramyan, L., Barker, A., Belkov, P. (2004). Sovremennyye tendentsii v antropologicheskikh issledovaniyakh. <em>Antropologicheskiy forum</em>, 1, 6–101.</li>
            <li>2. Agapkin, I.I. (2018). Ideya «kosmo-psikho-logosa» v tvorcheskom nasledii G.D. Gacheva. <em>Vestnik Russkoy khristianskoy gumanitarnoy akademii</em>, 19(2), 261–268.</li>
            <li>3. Baryshnikov, P.N. (2010). <em>Mif i metafora: lingvofilosofskiy podkhod</em>. Sankt-Peterburg: Aleteyya.</li>
            <li>4. Gumbol'dt, fon V. (2000). <em>Izbrannyye trudy po yazykoznaniyu</em> (2-ye izd.). Moskva: Progress.</li>
          </ul>
          <p class="mb-3">Если статья написана не на английском языке, список использованной литературы приводится в двух вариантах:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>первый список – полностью на латинице (при этом источники на русском языке приводятся в латинской транслитерации);</li>
            <li>второй список – полностью на английском языке; при этом в конце источников, оригинал которых опубликован не на английском языке, в скобках указывается язык оригинала, например: (in Russian), (in Uzbek) и т.д.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">III. Порядок рецензирования статей</h4>
          <ul class="list-disc list-inside space-y-1">
            <li>1. Поступившая статья первоначально проходит техническую проверку, затем проверяется на антиплагиат и, после установления её соответствия установленным требованиям, направляется на рецензирование. Сведения о рецензентах не сообщаются автору статьи. В свою очередь, рецензентам также не раскрываются сведения об авторах.</li>
            <li>2. Редакция не публикует заказные статьи на коммерческой основе и не гарантирует публикацию статьи в сроки, указанные автором. Редакция оставляет за собой право вносить в статью необходимые редакторские исправления и сокращения.</li>
            <li>3. Если статья направляется автору на доработку, после внесения необходимых изменений она повторно передаётся редактору для рецензирования. Если по результатам повторного рецензирования статья снова требует доработки, данный процесс продолжается до получения положительного заключения.</li>
            <li>4. Статьи, направленные редакционной коллегией на доработку, рассматриваются как вновь поступившие материалы и принимаются к рассмотрению для того номера, в период подготовки которого они были повторно представлены. Статьи, в которых выявлен плагиат, возвращаются автору для внесения необходимых исправлений и повторно проходят проверку на антиплагиат. Сотрудничество с автором продолжается до достижения уровня оригинальности не менее 80 %.</li>
            <li>5. После получения положительной рецензии редакция принимает решение о возможности публикации статьи в журнале.</li>
            <li>6. ВНИМАНИЕ! На всех этапах работы со статьями, а также при взаимодействии с авторами эксперт и редакция используют электронную почту. Авторы должны правильно указывать адрес электронной почты и своевременно сообщать о его изменении. Если статья подготовлена в соавторстве, переписка ведётся с одним из авторов – «корреспондирующим автором».</li>
            <li>7. Редакция не рассматривает обращения авторов по поводу принятых решений в отношении статьи, замечаний рецензентов, а также иных вопросов, связанных с порядком представления, оформления, рецензирования и публикации статей. Заключение по статье является коллегиальным решением редакции.</li>
            <li>8. Статьи, прошедшие рецензирование, возврату не подлежат.</li>
            <li>9. Автор (авторы) несёт ответственность за научные и фактические ошибки, а также за качество перевода аннотации. В подобных случаях автор (авторы) повторно представляет(ют) статью эксперту с внесёнными исправлениями и приложением обоснованных пояснений.</li>
            <li>10. После вёрстки статьи внесение существенных изменений не допускается. Автор имеет право отказаться от публикации статьи, однако оплата за рецензирование является обязательной.</li>
            <li>11. Научные взгляды автора статьи могут не совпадать с позицией редакции.</li>
            <li>12. Редакция просит авторов соблюдать нормы этики научной дискуссии, воздерживаться от необоснованных оценочных суждений, а также от некорректных высказываний в адрес установленных правил и экспертных заключений.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">IV. Политика журнала</h4>
          <p class="mb-2"><strong>Политика журнала в отношении применения искусственного интеллекта при подготовке научно-методических статей</strong></p>
          <p class="mb-4">Автор (авторы) обязаны открыто указывать случаи использования искусственного интеллекта в процессе подготовки статьи. Искусственный интеллект не может указываться в качестве автора статьи, а полная ответственность за содержание статьи возлагается на автора (авторов).</p>
          <p class="mb-4">Допускается использование искусственного интеллекта в целях языкового редактирования, перевода и стилистического улучшения текста. Категорически запрещается использование искусственного интеллекта для создания научных результатов и аналитических выводов, а также приведение недостоверных сведений и фиктивных источников.</p>
          <p class="mb-4">ВНИМАНИЕ! В статье, представляемой в журнал, обязательно должно содержаться следующее заявление. Например:</p>
          <p class="mb-4"><em>«При подготовке данной статьи средства искусственного интеллекта использовались исключительно в целях языкового редактирования и стилистического улучшения текста. Научное содержание, анализ и выводы принадлежат автору».</em></p>
          <p class="mb-3">Если искусственный интеллект не использовался:</p>
          <p class="mb-0"><em>«Автор не использовал искусственный интеллект при подготовке данной статьи».</em></p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">V. Авторские права</h4>
          <p class="mb-4">Направляя статью в редакцию, авторы выражают согласие на её публикацию в журнале «Вопросы филологии» в электронной форме без выплаты гонорара. В случае публикации статьи в данном журнале авторы передают авторские права на свои статьи Узбекскому государственному университету мировых языков. Авторы статей, принятых к публикации, заключают авторский договор. Полный текст договора размещён в разделе «Авторам» на сайте журнала.</p>
          <p class="mb-0">Авторы сохраняют право использовать свои материалы в последующих публикациях при обязательном указании ссылки на публикацию в журнале «Вопросы филологии». Кроме того, в соответствии с Законом Республики Узбекистан «О персональных данных» № ЗРУ-547 от 2 июля 2019 года авторы, публикующие свои статьи, выражают согласие Узбекскому государственному университету мировых языков на обработку предоставленных персональных данных, включая их сбор, систематизацию, накопление, хранение, уточнение (обновление, изменение), использование и уничтожение. Данное согласие подтверждается личной сканированной подписью автора (авторов) и предоставляется вместе с материалами, направляемыми для публикации. Настоящее согласие предоставляется автором (авторами) на неопределённый срок и может быть отозвано путём направления письменного уведомления.</p>
        </section>
        '''
    },
    'editorial_policy': {
        'title': 'Editorial policies',
        'title_uz': 'Tahririyat siyosati',
        'title_ru': 'Редакционная политика',
        'content': '''
        <section class="mb-8">
          <p class="mb-4">The following policies apply to the electronic scientific-methodological journal <strong>Philology Matters</strong>.</p>
          <p class="mb-0">Please read these policies in full before submitting your article, to ensure you've correctly followed all the requirements.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Affiliations</h4>
          <p class="mb-3">You and your co-authors must provide all relevant affiliations (in three languages (Uzbek, English, and Russian (or the language of the article)) identifying the institution(s) where the research or scholarly work was approved, supported, and/or conducted:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Full name(s) of the author(s) (in three languages);</li>
            <li>Academic degree(s), title(s), and position(s) of the author(s) (in three languages);</li>
            <li>Name of the region/place of residence of the author(s) (in three languages);</li>
            <li>E-mail address(es) of the author(s);</li>
            <li>ORCID iD(s) of the author(s);</li>
            <li>Contact phone number(s) of the author(s).</li>
          </ul>
          <p class="mb-2">If available:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Google Scholar profile link(s) of the author(s);</li>
            <li>Scopus Author profile link(s) of the author(s).</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Appeals and complaints</h4>
          <p class="mb-4">The editorial office of the electronic scientific-methodological journal Philology Matters follows the guidelines of the Committee on Publication Ethics (COPE) on appeals to journal editor decisions and complaints about a journal's editorial management of the peer review process.</p>
          <p class="mb-4">We welcome genuine appeals to the editor's decisions. However, you will need to provide strong evidence or new data/information in response to the editor's and reviewers' comments.</p>
          <p class="mb-4">If you, as an author, wish to comment on aspects of the journal's editorial management, please contact us and select "Other" as the topic.</p>
          <p class="mb-0">Please read the full guidance of the electronic scientific-methodological journal Philology Matters on peer review appeals and complaints from authors.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Authorship</h4>
          <p class="mb-4">Listing authors' names on an article is an important mechanism to give credit to those who have significantly contributed to the work. It also ensures transparency for those who are responsible for the integrity of the content.</p>
          <p class="mb-3">Authors listed in the article must meet all of the following criteria:</p>
          <ol class="list-decimal list-inside space-y-2">
            <li>made a significant contribution to the work reported, whether that's in the conception, design, implementation, data collection, analysis, and interpretation of the study, or in all these areas;</li>
            <li>have participated in drafting, writing, substantially revising, or critically reviewing the manuscript;</li>
            <li>have agreed on the journal to which the article will be submitted;</li>
            <li>have reviewed and agreed on all versions of the article prior to submission, during the revision process, the final version accepted for publication, as well as any significant changes introduced at the proofreading stage;</li>
            <li>agree to take responsibility and be accountable for the contents of the article and to share responsibility to resolve any questions raised about the accuracy or integrity of the published work.</li>
          </ol>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Defining authorship</h4>
          <p class="mb-4">It is the collective responsibility of all the individuals who have conducted the work to determine who should be listed as authors, and the order in which authors should be listed.</p>
          <p class="mb-4">The journal editor will not decide on the order of authorship and cannot arbitrate authorship disputes. Where unresolved disputes between the authors arise, the institution(s) where the work was performed will be asked to investigate.</p>
          <p class="mb-3">Please refer to our guide to defining authorship, which includes detailed information on the following:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Corresponding authors;</li>
            <li>Changes in authorship;</li>
            <li>Assistance from scientific writers or translators;</li>
            <li>Acknowledging use of AI;</li>
            <li>Assistance with experiments and data analysis;</li>
            <li>Acknowledgements;</li>
            <li>Author name change policy.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Citations</h4>
          <p class="mb-4">Research articles must cite relevant, timely, and verified literature (peer-reviewed, where appropriate) to support any claims made in the article.</p>
          <p class="mb-4">You must avoid excessive and inappropriate self-citation or prearrangements among author groups to inappropriately cite each other's work, as this can be considered a form of misconduct called citation manipulation. Read the COPE guidance on citation manipulation.</p>
          <p class="mb-4">If you are the author of a non-research article (for example, a Review or Opinion), you should ensure that all cited references are relevant and that the manuscript presents a fair and balanced overview of the current state of research or scholarly work in the field. Your references should not be unfairly biased towards a particular research group, organization or journal.</p>
          <p class="mb-4">If you are uncertain about how to cite a source correctly, you are encouraged to contact the journal editorial office for guidance.</p>
          <p class="mb-0">Please read the full citation guidance of the electronic scientific-methodological journal Philology Matters, including recommendations on the sources that should be added to your references list of your manuscript.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Competing interests</h4>
          <p class="mb-3">You and all of your co-authors must declare any competing interests relevant to, or which can be perceived to be relevant to the article.</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>A competing interest can occur where you (or your employer, sponsor or family/friends) have a financial, commercial, legal, or professional relationship with other organizations, or with the people working with them which could influence the research or interpretation of the results.</li>
            <li>Competing interests can be financial or non-financial in nature. To ensure transparency, you must also declare any associations which can be perceived by others as a competing interest.</li>
          </ul>
          <p class="mb-0">Please read our guide to competing interests. This includes examples of both financial and non-financial competing interests.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Corrections, expressions of concern, and retractions</h4>
          <p class="mb-4">Sometimes, after an article has been published, it may be necessary to make a change to the Version of Record (VoR). This will be done after careful consideration by the Editor with the support of the editorial staff of the electronic scientific-methodological journal Philology Matters, to ensure any necessary changes are made in accordance with guidance from the Committee on Publication Ethics (COPE).</p>
          <p class="mb-4">Any necessary changes will be accompanied with a post-publication notice which will be permanently linked to the original article. This can be in the form of a Correction notice, an Expression of Concern, a Retraction and in rare circumstances a Removal. The purpose of this mechanism of making changes which are permanent and transparent is to ensure the integrity of the scholarly record.</p>
          <p class="mb-0">Read our full policy on corrections, retractions, and updates to published articles.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Data availability and deposition</h4>
          <p class="mb-4">Are you submitting your paper to the electronic scientific-methodological journal Philology Matters, and is there a data set associated with your research? The journal has a data sharing policy that outlines how research data related to your article should be shared. The guide to understanding our data sharing policy provides detailed information and practical steps you'll need to take as an author.</p>
          <p class="mb-0">A data repository is a storage space for researchers to deposit data sets associated with their research. If you're an author seeking to comply with a journal data sharing policy, you'll need to identify a suitable repository for your data. Read our guide to choosing a data repository, which includes some generalist repository options that you may consider for storing and sharing your research data.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Custom computer codes, software tools, and mathematical algorithms</h4>
          <p class="mb-0">To enable full assessment of submissions, you must make available on request to Editors and/or reviewers any custom computer codes, software tools, or algorithms which have been used to generate the results and conclusions that are reported in your manuscript.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Designations of territories</h4>
          <p class="mb-4">The electronic scientific-methodological journal Philology Matters respects its authors' decisions regarding the designations of territories in its published material.</p>
          <p class="mb-4">The journal's policy is to take a neutral stance in relation to territorial disputes or jurisdictional claims in its published content, including in maps and institutional affiliations.</p>
          <p class="mb-0">Where a journal is owned by and published on behalf of a society or other third party, the editorial office of the journal will take into consideration the extent to which the policies of that society or third party may differ on this matter.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Editor Code of Conduct</h4>
          <p class="mb-4">The electronic scientific-methodological journal Philology Matters provides a platform for reliable and high-quality research evaluated by leading scholars and experts from around the world. The editor of a journal plays a crucial role in advancing knowledge within the relevant fields of research. They do this by:</p>
          <ul class="list-none space-y-1 mb-4">
            <li>&#10003; maintaining and improving the quality of articles published in the journal, as well as preserving the integrity of the peer review process;</li>
            <li>&#10003; supporting the journal's authors and reviewers;</li>
            <li>&#10003; maintaining and enhancing the journal's reputation in cooperation with the editorial team.</li>
          </ul>
          <p class="mb-0">To support this role, the Editorial Code of Conduct of the electronic scientific-methodological journal Philology Matters establishes minimum standards for journal editors who have responsibility for decisions on journal content to help ensure our journals publish quality, trustworthy content.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Funding</h4>
          <p class="mb-4">The electronic scientific-methodological journal Philology Matters requires authors to declare all sources of financial support that contributed to covering the research expenses related to the work presented in their articles. Examples of these funding sources include:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>internal funds, grants, and other forms of financial support provided by the authors' institutions, employers, or affiliated organizations;</li>
            <li>external funds received from charitable or non-profit organizations, private foundations, commercial companies (e.g. technological or pharmaceutical companies), think tanks, advocacy groups, research associations, and governmental bodies.</li>
          </ul>
          <p class="mb-4">The funding declaration enables authors to attribute credit to funders and facilitates transparency, especially where the funder may have additional roles or may have contributed to the research study. These contributions would also need to be defined in more detail within the competing interests declaration.</p>
          <p class="mb-3">Authors should declare financial support used for, including but not limited to, the following purposes:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Funding used to cover the expense associated with performing the research (e.g. costs of equipment or reagents used in the study) and/or analysis of the results;</li>
            <li>External assistance or funding used for experiments, comparisons, and/or data analysis presented in the manuscript;</li>
            <li>Additional funding used to cover language editing services, translators, or academic writing assistance;</li>
            <li>Travel funding required for the implementation of the research project.</li>
          </ul>
          <p class="mb-4">Authors are expected to declare only those funds and grants that are directly related to the work presented in their article. If no funding was received for the reported work, authors are encouraged to declare that no funding was obtained. This ensures transparency and avoids concerns being raised about undeclared funding support.</p>
          <p class="mb-4">Any funding declaration must include the full name(s) of the funding body, the grant number(s), and, where possible, the name of the individual or research group to whom this grant was awarded. If the funder also played an active role in the research process, such as the data collection or analysis, this should be clearly stated in the competing interests declaration.</p>
          <p class="mb-0">Authors must be prepared to provide funding documentation and additional information to the editorial office if requested. Failure to disclose funding may, in certain cases, be regarded as a form of misconduct and may result in corrective action to ensure the integrity of the scholarly record.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Harassment</h4>
          <p class="mb-4">The electronic scientific-methodological journal Philology Matters does not tolerate any form of harassment, intimidation, or undue pressure directed toward authors, editors, reviewers, editorial staff, or vendors.</p>
          <p class="mb-4">The editorial office is committed to maintaining a professional environment based on mutual respect and will work with the publisher's ethics officers and legal representatives to deal with any cases of harassment.</p>
          <p class="mb-0">Guidance for researchers experiencing harassment: As a researcher, you should expect that your work may attract public attention and be subject to scrutiny by the public, policymakers, and advocacy groups. However, researchers working on high-profile or controversial topics may also encounter online harassment. To assist researchers in addressing such challenges, the electronic scientific-methodological journal Philology Matters recommends consulting its guide on responding to social media harassment.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Images and figures</h4>
          <p class="mb-4">You should include images and illustrations in your article only if they are relevant and valuable to the work reported. Please avoid the inclusion of visual materials that do not contribute to the scholarly content of the article.</p>
          <p class="mb-4">Please read the journal's policy on images and illustrations for further guidance.</p>
          <p class="mb-4">As a warranty in the Journal Author Publishing Agreement you make with the electronic scientific-methodological journal Philology Matters, you must obtain the necessary written permission to include material in your article that is owned and held in copyright by a third party. Such materials may include, but are not limited to, proprietary text, illustrations, tables, audio or video materials, film stills, screenshots, musical notations, and any supplemental material.</p>
          <p class="mb-4">Read the journal's guide to using third-party materials in your article, including FAQs on requesting permission to reproduce work(s) under copyright.</p>
          <p class="mb-4">Content (e.g. photographs, video or audio recordings, 3D models, illustrations, etc) which can reveal the identity of patients, study participants or study subjects can only be included if they (or parents/guardians if they are underage or considered unable to provide informed consent, or their next of kin if participants are deceased) have provided consent to publish.</p>
          <p class="mb-0">If any of this type of content has been obtained from communities where additional permissions are required (e.g. an Elder or community leader in an indigenous community), or from a protected source (e.g. museum collections), then authors must obtain the required permissions for use prior to submission of the manuscript.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Misconduct</h4>
          <p class="mb-3">The electronic scientific-methodological journal Philology Matters takes all forms of misconduct seriously and will take all necessary measures, in accordance with COPE guidelines, to protect the integrity of the scholarly record.</p>
          <p class="mb-3">Examples of misconduct include, but are not limited to:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Affiliation misrepresentation;</li>
            <li>Breaches in copyright/the use of third-party material without appropriate permission;</li>
            <li>Citation manipulation;</li>
            <li>Duplicate submission/publication;</li>
            <li>"Ethics dumping";</li>
            <li>Image or data manipulation/fabrication;</li>
            <li>Peer review process manipulation;</li>
            <li>Plagiarism;</li>
            <li>Text recycling/self-plagiarism;</li>
            <li>Undisclosed competing interests;</li>
            <li>Unethical research practices.</li>
          </ul>
          <p class="mb-0">Read the full policy to find out more about the areas of misconduct listed above.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Peer review</h4>
          <p class="mb-4">Articles submitted to the electronic scientific-methodological journal Philology Matters, including draft versions, undergo thorough peer review. The journal follows COPE guidelines for reviewers. The guide to understanding the double-blind peer review process may be useful in this regard.</p>
          <p class="mb-4">The electronic scientific-methodological journal Philology Matters publishes a statement describing the model of peer review used by the journal on the journal homepage. Each research article normally requires evaluation by at least two independent reviewers. The journal's aims and scope provide detailed information on its double-blind peer review policy.</p>
          <p class="mb-4">The details of the reviewers' comments, together with their overall recommendations, are taken into consideration by the editor when making a decision; however, the final responsibility for accepting or rejecting a manuscript lies with the Editor.</p>
          <p class="mb-4">In accordance with COPE Ethical Guidelines for new Editors, Editors must delegate any submissions that they are unable to handle impartially (e.g. if they are the author of the submitted manuscript) to a member of the Editorial Board or to a guest editor.</p>
          <p class="mb-4">Please note that the electronic scientific-methodological journal Philology Matters does not permit authors to recommend reviewers for their manuscripts.</p>
          <p class="mb-3"><strong>Confidentiality of peer review</strong></p>
          <p class="mb-4">It is a requirement to maintain confidentiality and integrity of the peer review and editorial decision-making process at all stages, complying with data protection regulations, including the GDPR. The invited reviewer should declare any competing interests before submitting their review report to the journal. If a reviewer wishes to involve a colleague as a co-reviewer for an article, prior approval from the editorial office must be obtained before the manuscript is reviewed, and the colleague's full name, affiliation, and any relevant competing interests must be declared to the editorial office when submitting the review report.</p>
          <p class="mb-0">In the process of investigating an ethical query, the submitted manuscript, author, reviewer, and any other person (including whistleblowers) involved will be treated in confidence. During an investigation, the editor may need to share relevant information with third parties, such as ethics committees or the authors' institutions.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Plagiarism</h4>
          <p class="mb-4">Trust and integrity are among the most highly valued principles in scholarly peer-reviewed publishing. For this reason, the electronic scientific-methodological journal Philology Matters takes the issue of plagiarism very seriously.</p>
          <p class="mb-4">For Philology Matters, plagiarism includes the unauthorized use of information, images, words, or ideas taken from any material published in electronic or print form. Any direct or indirect use of such material must be properly acknowledged in all instances. You should provide appropriate citations and clearly indicate the source at all times.</p>
          <p class="mb-0">Please read the journal's plagiarism policy and guidance for authors to find out what plagiarism is (and isn't) and how you can avoid it.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Preprints, Preprint Servers, and Early Reporting of Scholarly Work</h4>
          <p class="mb-4">The electronic scientific-methodological journal Philology Matters supports the need for authors to share early versions of their work before peer review publication. Authors are provided with several options for sharing the final Version of Record of their published article.</p>
          <p class="mb-4">A preprint, also known as the Author's Original Manuscript (AOM), is the version of your article prior to its submission to a journal for peer review. Preprint servers are online repositories which enable you to post an early version of your research paper online.</p>
          <p class="mb-4">If you upload your AOM to a non-commercial preprint server, you can subsequently submit the manuscript to the electronic scientific-methodological journal Philology Matters. The journal does not consider posting on a preprint to be duplicate publication and this will not jeopardize consideration for publication.</p>
          <p class="mb-0">If you have published an article in the electronic scientific-methodological journal Philology Matters, you may share it with colleagues and peers through various channels and platforms. Read our guide to sharing your work.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Research ethics and consent</h4>
          <p class="mb-0">All research published in the electronic scientific-methodological journal Philology Matters must have been conducted according to international and local guidelines ensuring ethically conducted research.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Standards of reporting</h4>
          <p class="mb-0">Research should be communicated in a manner that ensures transparency, verification, and reproducibility. Therefore, authors are encouraged to provide comprehensive descriptions of the study rationale, protocol, methodology, and analysis. To assist authors in this process, several study-design specific consensus-based reporting guidelines have been developed, and we recommend you to use these as guidance prior to submitting your manuscript.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Use of third-party material</h4>
          <p class="mb-4">You must obtain the necessary permission to reuse third-party materials included in your article. Such materials may include, but are not limited to, text, illustrations, photographs, tables, datasets, audio and video materials, film stills, screenshots, and musical notations.</p>
          <p class="mb-4">Brief excerpts of text and certain other categories of material may generally be used in limited amounts for criticism or review without formal permission. However, if you wish to include any material in your manuscript for which you do not hold copyright and which is not covered by such exceptions, you will need to obtain written permission from the copyright owner prior to submission.</p>
          <p class="mb-4">Further resources on copyright services are available on our website in the detailed FAQ section, covering topics such as quotes and screenshots from X (former Twitter), old paintings, redrawn images and derivative copyrighted materials, the quotations of poetry or songs, and guidance on the use of third-party content in open access articles.</p>
          <p class="mb-0">Read more information on requesting permission to reproduce work(s) under copyright.</p>
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
          <p class="mb-4">К электронному научно-методическому журналу <strong>«Вопросы филологии»</strong> применяются следующие правила.</p>
          <p class="mb-0">Пожалуйста, внимательно ознакомьтесь с этими правилами перед отправкой статьи, чтобы убедиться, что вы правильно выполнили все требования.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Аффилиации</h4>
          <p class="mb-3">Для всех авторов и соавторов необходимо указать все соответствующие аффилиации, идентифицирующие учреждение (учреждения), в котором (которых) было одобрено, поддержано и/или проведено исследование или научная работа, включая:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>полные фамилии и имена авторов (на узбекском, русском и английском языках);</li>
            <li>ученые степени, звания и должности авторов (на узбекском, русском и английском языках);</li>
            <li>название региона/страны проживания авторов (на узбекском, русском и английском языках);</li>
            <li>адреса электронной почты авторов;</li>
            <li>идентификаторы ORCID авторов;</li>
            <li>номера телефонов авторов.</li>
          </ul>
          <p class="mb-2">При наличии авторы также должны предоставить:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>ссылки на свои профили в Google Scholar и Scopus.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Апелляции и жалобы</h4>
          <p class="mb-4">Электронный научно-методический журнал «Вопросы филологии» принимает жалобы на решения редакторов и на редакционное управление процессом публикации журнала в соответствии с рекомендациями Комитета по публикационной этике (Committee on Publication Ethics, COPE).</p>
          <p class="mb-4">Редакция электронного научно-методического журнала «Вопросы филологии» руководствуется рекомендациями Комитета по публикационной этике (COPE) в отношении апелляций на решения редакции журнала и жалоб на редакционное управление процессом рецензирования.</p>
          <p class="mb-4">Мы приветствуем обоснованные апелляции на решения редактора. Однако вам необходимо будет предоставить веские доказательства или новые данные/информацию в ответ на замечания редактора и рецензентов.</p>
          <p class="mb-4">Если Вы как автор желаете высказать замечания по вопросам редакционной политики журнала, пожалуйста, свяжитесь с нами и выберите тему «Другое».</p>
          <p class="mb-0">Ознакомьтесь с полным руководством электронного научно-методического журнала «Вопросы филологии» по обжалованию рецензирования и жалобам авторов.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Авторство</h4>
          <p class="mb-4">Указание имен авторов в статье является важным механизмом признания заслуг тех, кто внес значительный вклад в работу. Это также обеспечивает прозрачность для тех, кто несет ответственность за целостность содержания.</p>
          <p class="mb-3">Авторы, указанные в статье, должны соответствовать всем следующим критериям:</p>
          <ol class="list-decimal list-inside space-y-2">
            <li>внесли значительный вклад в представленную работу, будь то в разработке концепции, планировании, реализации, сборе данных, анализе и интерпретации результатов исследования, либо во всех этих областях;</li>
            <li>участвовали в составлении, написании, существенной доработке или критическом рецензировании рукописи;</li>
            <li>согласились с выбором журнала, в который будет отправлена статья;</li>
            <li>ознакомились и согласовали все версии статьи до подачи, в процессе редактирования, окончательную версию, принятую к публикации, а также любые существенные изменения, внесенные на этапе корректуры;</li>
            <li>согласились взять на себя ответственность и нести ответственность за содержание статьи, а также разделять ответственность за решение любых вопросов, возникающих в отношении точности или целостности опубликованной работы.</li>
          </ol>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Определение авторства</h4>
          <p class="mb-4">Определение того, кто должен быть указан в качестве авторов, и порядка их перечисления является коллективной ответственностью всех лиц, выполнивших работу.</p>
          <p class="mb-4">Редактор журнала не принимает решения о порядке указания авторов и не может выступать арбитром в спорах об авторстве. В случае возникновения неразрешенных споров между авторами, учреждению (учреждениям), в котором (которых) была выполнена работа, будет предложено провести расследование.</p>
          <p class="mb-3">Ознакомьтесь с нашим руководством по определению авторства, в котором содержится подробная информация по следующим вопросам:</p>
          <ul class="list-disc list-inside space-y-1">
            <li>Авторы, контактирующие с редакцией;</li>
            <li>Изменения в авторстве;</li>
            <li>Помощь научных редакторов или переводчиков;</li>
            <li>Указание на использование ИИ;</li>
            <li>Помощь в проведении экспериментов и анализе данных;</li>
            <li>Благодарности;</li>
            <li>Политика изменения имени автора.</li>
          </ul>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Цитирование</h4>
          <p class="mb-4">В научных статьях должны цитироваться актуальные, своевременные и проверенные источники (прошедшие экспертную оценку, где это уместно) для подтверждения любых утверждений, сделанных в статье.</p>
          <p class="mb-4">Необходимо избегать чрезмерных и неуместных самоцитирований или предварительных договоренностей между группами авторов о взаимном цитировании работ друг друга, так как это может рассматриваться как форма недобросовестного поведения, называемая манипуляцией цитированием. Ознакомьтесь с рекомендациями COPE по манипуляции цитированием.</p>
          <p class="mb-4">Если вы являетесь автором статьи, не относящейся к научным исследованиям (например, рецензии или мнения), вы должны убедиться в достоверности приведенных ссылок и объективно и сбалансированно оценить текущее состояние исследований или научной работы по данной теме. Ваши материалы не должны быть предвзятыми по отношению к какой-либо исследовательской группе, организации или журналу.</p>
          <p class="mb-4">Если вы являетесь автором неисследовательской статьи (например, Обзора), вам следует убедиться, что все цитируемые источники являются актуальными и что рукопись представляет объективный и сбалансированный обзор текущего состояния исследований или научной работы в данной области. Ваши ссылки не должны быть предвзятыми в отношении конкретной исследовательской группы, организации или журнала.</p>
          <p class="mb-4">Если вы не уверены, как правильно цитировать источник, рекомендуем обратиться за консультацией в редакцию журнала.</p>
          <p class="mb-0">Пожалуйста, ознакомьтесь с полным руководством по цитированию электронного научно-методического журнала «Вопросы филологии», включая рекомендации по источникам, которые следует включить в список литературы вашей рукописи.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Конфликт интересов</h4>
          <p class="mb-3">Вы и все ваши соавторы обязаны заявлять о любых конфликтах интересов, имеющих отношение к статье или которые могут быть восприняты как имеющие к ней отношение.</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Конфликт интересов может возникнуть в том случае, если у вас (или у вашего работодателя, спонсора, семьи или друзей) имеются финансовые, коммерческие, юридические или профессиональные отношения с другими организациями или с людьми, работающими в них, которые могут повлиять на исследование или интерпретацию его результатов.</li>
            <li>Конфликт интересов может носить как финансовый, так и нефинансовый характер. Для обеспечения прозрачности вы также должны заявить о любых связях, которые могут быть восприняты другими как конфликт интересов.</li>
          </ul>
          <p class="mb-0">Пожалуйста, ознакомьтесь с нашим руководством по конфликту интересов. В нем приведены примеры как финансового, так и нефинансового конфликта интересов.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Исправления, выражения озабоченности и отзывы</h4>
          <p class="mb-4">Иногда после публикации статьи может возникнуть необходимость внести изменения в окончательную версию (Version of Record, VoR). Это будет сделано после тщательного рассмотрения редактором при поддержке редакционного коллектива электронного научно-методического журнала «Вопросы филологии», чтобы гарантировать, что все необходимые изменения внесены в соответствии с рекомендациями Комитета по публикационной этике (COPE).</p>
          <p class="mb-4">Любые необходимые изменения будут сопровождаться уведомлением после публикации, которое будет постоянно связано с исходной статьей. Это может быть в форме уведомления об исправлении, выражения озабоченности, отзыва и, в редких случаях, удаления. Цель этого механизма внесения постоянных и прозрачных изменений заключается в обеспечении целостности научной документации.</p>
          <p class="mb-0">Ознакомьтесь с нашей полной политикой в отношении исправлений, отзывов и обновлений опубликованных статей.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Доступность и хранение данных</h4>
          <p class="mb-3"><strong>Политика обмена данными</strong></p>
          <p class="mb-4">Вы планируете подать свою статью в электронный научно-методический журнал «Вопросы филологии» и у вас есть пакет документов, связанных с вашей работой? В данном журнале существует политика обмена информацией, определяющая, каким образом следует обмениваться информацией, связанной с вашей статьей. Руководство для понимания политики обмена данными журнала подробно ознакомит вас с деталями и шагами, которые вам необходимо выполнить в качестве участника этого процесса.</p>
          <p class="mb-3"><strong>Хранилище данных</strong></p>
          <p class="mb-4">Хранилище данных – это хранилище, в котором исследователи могут размещать данные, связанные с их исследованиями. Если вы являетесь автором и стремитесь соблюдать политику журнала в отношении обмена данными, вам необходимо выбрать подходящее хранилище для ваших данных.</p>
          <p class="mb-0">Ознакомьтесь с нашим руководством по выбору хранилища данных, в котором представлены некоторые универсальные варианты хранилищ, которые вы можете рассмотреть для хранения и обмена данными ваших исследований.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Индивидуальные компьютерные коды, программные инструменты и математические алгоритмы</h4>
          <p class="mb-0">Для обеспечения полноценной оценки представленных материалов вы должны предоставить по запросу редакторов и/или рецензентов любые пользовательские компьютерные коды, программные инструменты или алгоритмы, которые были использованы для получения результатов и выводов, представленных в вашей рукописи.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Обозначения территорий</h4>
          <p class="mb-4">Электронный научно-методический журнал «Вопросы филологии» уважает решения своих авторов относительно обозначения территорий в публикуемых материалах.</p>
          <p class="mb-4">Политика журнала заключается в том, чтобы занимать нейтральную позицию в отношении территориальных споров или юрисдикционных претензий в публикуемом контенте, включая карты и указания на принадлежность к организациям.</p>
          <p class="mb-0">Если журнал принадлежит и издается от имени общества или иной третьей стороны, редакция журнала будет учитывать степень, в которой политика данного общества или третьей стороны может отличаться в этом вопросе.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Кодекс поведения редактора</h4>
          <p class="mb-4">Электронный научно-методический журнал «Вопросы филологии» предоставляет платформу для надежных и высококачественных исследований, оцениваемых ведущими учеными и экспертами со всего мира. Редактор журнала играет ключевую роль в продвижении знаний в соответствующих областях исследований. Он делает это путем:</p>
          <ul class="list-none space-y-1 mb-4">
            <li>&#10003; поддержания и повышения качества статей, публикуемых в журнале, а также обеспечения честности и объективности процесса рецензирования;</li>
            <li>&#10003; поддержки авторов и рецензентов журнала;</li>
            <li>&#10003; поддержки и укрепления репутации журнала в сотрудничестве с редакционной коллегией.</li>
          </ul>
          <p class="mb-0">В целях поддержки этой роли Кодекс профессиональной этики редакции электронного научно-методического журнала «Вопросы филологии» устанавливает необходимые стандарты для редакторов журнала, которые несут ответственность за принятие решений относительно содержания журнала, чтобы помочь обеспечить публикацию в наших журналах качественного и достоверного контента.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Финансирование</h4>
          <p class="mb-4">Электронный научно-методический журнал «Вопросы филологии» требует от авторов декларировать все источники финансовой поддержки, которые способствовали покрытию расходов на исследования, связанных с работами, представленными в их статьях. Примеры таких источников финансирования включают:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>внутренние средства, гранты и другие формы финансовой поддержки, предоставляемые учреждениями авторов, их работодателями или аффилированными организациями;</li>
            <li>внешние средства, полученные от благотворительных или некоммерческих организаций, частных фондов, коммерческих компаний (например, технологических или фармацевтических компаний), аналитических центров, групп по защите интересов, исследовательских ассоциаций и государственных органов.</li>
          </ul>
          <p class="mb-4">Декларация о финансировании позволяет авторам выразить признательность спонсорам и способствует прозрачности, особенно в тех случаях, когда спонсор может играть дополнительные роли или вносить вклад в исследование. Эти вклады также необходимо более подробно описать в декларации о конфликте интересов.</p>
          <p class="mb-3">Авторы должны декларировать финансовую поддержку, использованную для следующих целей (не исключая иные цели, не перечисленные ниже):</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Финансирование, использованное для покрытия расходов, связанных с проведением исследования (например, расходы на оборудование или реагенты, использованные в исследовании) и/или анализом результатов;</li>
            <li>Внешняя помощь или финансирование, использованные для проведения экспериментов, сравнений и/или анализа данных, представленных в рукописи. Финансирование, использованное для оплаты услуг сторонних организаций или внешней помощи в проведении экспериментов, сборе и/или анализе данных, о которых сообщается в статье. Информацию об авторстве и признании внешней поддержки можно найти здесь;</li>
            <li>Дополнительное финансирование, использованное для оплаты услуг по редактированию текста, услуг переводчиков или помощи в написании научных работ. Наши правила в отношении авторства и указания поддержки можно найти здесь;</li>
            <li>Финансирование поездок, необходимое для реализации исследовательского проекта.</li>
          </ul>
          <p class="mb-4">Авторы должны указывать только те источники финансирования и гранты, которые имеют непосредственное отношение к работе, представленной в их статье. Если финансирование для описанной работы не предоставлялось, авторам рекомендуется указать, что финансирование не получалось. Это обеспечивает прозрачность и позволяет избежать подозрений в наличии незадекларированной финансовой поддержки.</p>
          <p class="mb-4">Любое заявление о финансировании должно содержать полное название финансирующей организации, номер(а) гранта и, по возможности, имя лица или название исследовательской группы, которой был предоставлен данный грант. Как указано выше, если финансирующая сторона также играла активную роль в процессе исследования, например, в сборе или анализе данных, это должно быть четко указано в заявлении о конфликте интересов.</p>
          <p class="mb-0">Авторы должны быть готовы предоставить в редакцию документацию о финансировании и дополнительную информацию по запросу (в том числе, при необходимости, информацию о средствах, использованных для оплаты сборов за подачу и публикацию). Обращаем ваше внимание на то, что нераскрытие информации о финансировании в некоторых случаях может рассматриваться как форма недобросовестного научного поведения и может привести к принятию корректирующих мер для обеспечения достоверности научной публикации. В случае выявления неточностей или отсутствия ключевой информации в заявлении о финансировании может потребоваться публикация уведомлений об исправлениях или отзыве (в зависимости от ситуации) в отношении опубликованных статей.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Публикационная этика автора</h4>
          <p class="mb-4">Электронный научно-методический журнал «Вопросы филологии» не допускает никаких форм домогательств, запугивания или неправомерного давления в отношении авторов, редакторов, рецензентов, сотрудников редакции или поставщиков.</p>
          <p class="mb-4">Редакция стремится поддерживать профессиональную среду, основанную на взаимном уважении, и будет сотрудничать с работниками издательства, ответственными за вопросы этики, а также с юридическими представителями для решения любых случаев домогательств.</p>
          <p class="mb-0">Рекомендации для исследователей, подвергающихся притеснениям. Как исследователь, вы должны быть готовы к тому, что ваша работа может привлечь внимание общественности и стать предметом тщательного изучения со стороны общественности, политиков и правозащитных групп. Однако исследователи, работающие над резонансными или спорными темами, могут также сталкиваться с буллингом в Интернете. Чтобы помочь исследователям справиться с такими проблемами, электронный научно-методический журнал «Вопросы филологии» рекомендует ознакомиться с его руководством по реагированию на притеснения и преследования в социальных сетях.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Изображения и рисунки</h4>
          <p class="mb-4">Вы должны включать изображения и иллюстрации в свою статью только в том случае, если они имеют отношение к описываемой работе и представляют ценность для нее. Пожалуйста, избегайте включения визуальных материалов, которые не вносят вклад в научное содержание статьи.</p>
          <p class="mb-0">Для получения дополнительных рекомендаций ознакомьтесь с политикой журнала в отношении изображений и иллюстраций.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Использование материалов третьих лиц</h4>
          <p class="mb-4">В соответствии с гарантиями, предусмотренными в Договоре о публикации статей, заключаемом вами с электронным научно-методическим журналом «Вопросы филологии», вы обязаны получить необходимое письменное разрешение на включение в свою статью материалов, права на которые принадлежат третьим лицам. К таким материалам могут относиться, в частности, тексты, иллюстрации, таблицы, аудио- или видеоматериалы, кадры из фильмов, скриншоты, нотные записи и любые дополнительные материалы.</p>
          <p class="mb-0">Ознакомьтесь с руководством журнала по использованию материалов третьих лиц в вашей статье, включая ответы на часто задаваемые вопросы о получении разрешения на воспроизведение произведений, защищенных авторским правом.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Получение разрешения на публикацию идентифицируемого или защищенного контента</h4>
          <p class="mb-4">Контент (например, фотографии, видео- или аудиозаписи, 3D-модели, иллюстрации и т. д.), который может раскрыть личность пациентов, участников или субъектов исследования, может быть включен только в том случае, если они (или родители/опекуны, если они несовершеннолетние или считаются неспособными дать информированное согласие, или ближайшие родственники, если участники умерли) дали согласие на публикацию.</p>
          <p class="mb-0">Если какой-либо контент данного типа был получен от сообществ, где требуются дополнительные разрешения (например, от старейшины или лидера общины коренного населения), или из защищенного источника (например, из музейных коллекций), авторы должны получить необходимые разрешения на использование до подачи рукописи. Для получения более подробной информации прочитайте полную политику журнала по использованию изображений и иллюстраций.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Нарушения</h4>
          <p class="mb-3">Электронный научно-методический журнал «Вопросы филологии» серьезно относится ко всем формам недобросовестного поведения и примет все необходимые меры в соответствии с руководящими принципами COPE для защиты целостности научной документации.</p>
          <p class="mb-3">Примеры недобросовестного поведения включают, но не ограничиваются:</p>
          <ul class="list-disc list-inside space-y-1 mb-4">
            <li>Ложные сведения об аффилиации;</li>
            <li>Нарушение авторских прав/использование материалов третьих лиц без соответствующего разрешения;</li>
            <li>Манипуляции с цитированием;</li>
            <li>Повторная подача/публикация;</li>
            <li>«Этический демпинг» (снижение этических стандартов);</li>
            <li>Манипулирование изображениями или данными/фальсификация;</li>
            <li>Манипулирование процессом рецензирования;</li>
            <li>Плагиат;</li>
            <li>Повторное использование текста/самоплагиат;</li>
            <li>Нераскрытые конфликты интересов;</li>
            <li>Неэтичные методы проведения исследований.</li>
          </ul>
          <p class="mb-0">Ознакомьтесь с полным текстом политики, чтобы узнать больше о перечисленных выше видах неправомерных действий.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Рецензирование</h4>
          <p class="mb-4">Статьи, представленные в электронный научно-методический журнал «Вопросы филологии», включая черновые версии, проходят тщательное рецензирование. Журнал следует рекомендациям COPE для рецензентов. В этом отношении может быть полезно руководство для понимания процесса двойного слепого рецензирования.</p>
          <p class="mb-4">Электронный научно-методический журнал «Вопросы филологии» публикует на главной странице журнала заявление, описывающее модель рецензирования, используемую журналом. Каждая научная статья, как правило, требует оценки как минимум двумя независимыми рецензентами. Цели и сфера деятельности журнала содержат подробную информацию о его политике двойного слепого рецензирования.</p>
          <p class="mb-4">При принятии решения редактор учитывает детали комментариев рецензентов, а также их общие рекомендации; однако окончательная ответственность за принятие или отклонение рукописи лежит на редакторе.</p>
          <p class="mb-4">В соответствии с Этическими рекомендациями COPE для новых редакторов, редакторы обязаны передавать на рассмотрение члену редакционной коллегии или приглашенному редактору все рукописи, которые они не могут рассмотреть беспристрастно (например, если они являются авторами представленной рукописи).</p>
          <p class="mb-4">Обращаем ваше внимание на то, что электронный научно-методический журнал «Вопросы филологии» не допускает, чтобы авторы предлагали кандидатуры рецензентов для своих рукописей.</p>
          <p class="mb-3"><strong>Конфиденциальность рецензирования</strong></p>
          <p class="mb-4">Обязательным требованием является соблюдение конфиденциальности и целостности процесса рецензирования и принятия редакционных решений на всех этапах в соответствии с нормами защиты данных, включая GDPR (Общий регламент по защите данных). Приглашенный рецензент должен заявить о любых конфликтах интересов до подачи своего отчета о рецензии в журнал. Если рецензент желает привлечь коллегу в качестве сорецензента для статьи, необходимо получить предварительное одобрение от редакции до начала рецензирования рукописи, а при подаче отчета о рецензии в редакцию необходимо указать полное имя коллеги, его принадлежность к организации и любые соответствующие конфликты интересов.</p>
          <p class="mb-0">В процессе расследования этического запроса представленная рукопись, автор, рецензент и любые другие вовлеченные лица (включая информаторов) будут рассматриваться конфиденциально. В ходе расследования редактору может потребоваться поделиться соответствующей информацией с третьими сторонами, такими как комитеты по этике или учреждения авторов.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Плагиат</h4>
          <p class="mb-4">Доверие и честность относятся к числу наиболее ценных принципов в научном рецензируемом издательстве. По этой причине электронный научно-методический журнал «Вопросы филологии» очень серьезно относится к проблеме плагиата.</p>
          <p class="mb-4">Для журнала «Вопросы филологии» плагиат включает в себя несанкционированное использование информации, изображений, слов или идей, взятых из любых материалов, опубликованных в электронной или печатной форме. Любое прямое или косвенное использование таких материалов должно быть должным образом указано во всех случаях. Вы должны всегда приводить соответствующие цитаты и четко указывать источник.</p>
          <p class="mb-0">Пожалуйста, ознакомьтесь с политикой журнала в отношении плагиата и рекомендациями для авторов, чтобы узнать, что является плагиатом (а что нет) и как его избежать.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Препринты, серверы препринтов и раннее опубликование научных работ</h4>
          <p class="mb-4">Электронный научно-методический журнал «Вопросы филологии» поддерживает необходимость обмена авторами ранними версиями своих работ до публикации по результатам рецензирования. Авторам предоставляется несколько вариантов обмена окончательной версией своей опубликованной статьи.</p>
          <p class="mb-3"><strong>Препринты и серверы препринтов</strong></p>
          <p class="mb-4">Препринт, также известный как авторский оригинал рукописи (AOM), представляет собой версию вашей статьи до ее подачи в журнал для рецензирования. Серверы препринтов – это онлайн-репозитории, которые позволяют размещать раннюю версию вашей научной статьи в Интернете.</p>
          <p class="mb-0">Если вы загрузите свой AOM на некоммерческий сервер препринтов, вы сможете впоследствии подать рукопись в электронный научно-методический журнал «Вопросы филологии». Журнал не считает публикацию на сервере препринтов дублированием публикации, и это не повлияет на рассмотрение вашей работы к публикации.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Распространение опубликованной статьи</h4>
          <p class="mb-4">Если вы опубликовали статью в электронном научно-методическом журнале «Вопросы филологии», вы можете поделиться ею с коллегами и единомышленниками через различные каналы и платформы.</p>
          <p class="mb-0">Ознакомьтесь с нашим руководством по распространению ваших работ.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Этика исследований и согласие</h4>
          <p class="mb-0">Все исследования, публикуемые в электронном научно-методическом журнале «Вопросы филологии», должны быть проведены в соответствии с международными и местными руководящими принципами, обеспечивающими этическое проведение исследований.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Стандарты представления результатов</h4>
          <p class="mb-4">Результаты исследований должны излагаться таким образом, чтобы обеспечить их прозрачность, проверяемость и воспроизводимость. В связи с этим авторам рекомендуется предоставлять исчерпывающие описания обоснования исследования, его протокола, методологии и анализа.</p>
          <p class="mb-0">Чтобы помочь авторам в этом процессе, было разработано несколько основанных на консенсусе рекомендаций по представлению результатов, специфичных для конкретных типов исследований, и мы рекомендуем вам использовать их в качестве руководства перед подачей рукописи.</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Использование материалов третьих лиц</h4>
          <p class="mb-4">Вы должны получить необходимое разрешение на повторное использование материалов третьих лиц, включенных в вашу статью. К таким материалам могут относиться, в том числе, текст, иллюстрации, фотографии, таблицы, наборы данных, аудио- и видеоматериалы, кадры из фильмов, скриншоты и нотные записи.</p>
          <p class="mb-4">Краткий отрывок текста и некоторые другие категории материалов, как правило, могут использоваться в ограниченных объемах для критики или рецензии без официального разрешения. Однако, если вы желаете включить в свою рукопись какие-либо материалы, на которые у вас нет авторских прав и которые не подпадают под такие исключения, вам необходимо получить письменное разрешение от владельца авторских прав до подачи рукописи.</p>
          <p class="mb-4">Дополнительные ресурсы по вопросам авторского права доступны на нашем веб-сайте в подробном разделе «Часто задаваемые вопросы», где освещаются такие темы, как цитаты и скриншоты из X (бывший Twitter), старинные картины, перерисованные изображения и производные материалы, защищенные авторским правом, цитаты из стихов или песен, а также рекомендации по использованию стороннего контента в статьях с открытым доступом.</p>
          <p class="mb-0">Узнайте больше о том, как запросить разрешение на воспроизведение произведений, защищенных авторским правом.</p>
        </section>
        '''
    },
    'site_editing_services': {
        'title': 'Site Editing Services',
        'title_uz': 'Tahrirlash xizmatlari',
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
        'title_ru': 'Цели и сфера деятельности',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Aims and Scope</h4>
          <p class="mb-4">The electronic scientific-methodological journal <strong>Philology Matters</strong> supports the publication of research conducted worldwide that advances knowledge, theory, and methodology at the intersection of Philology (10.00.00) and Pedagogy (13.00.00). The journal focuses on the role of language and other philological issues in relation to pedagogical challenges associated with the learning, teaching, and acquisition of first (native), second, and foreign languages in the world.</p>
          <p class="mb-4">The journal publishes research aimed at providing the scholarly community with opportunities to disseminate original research findings; drawing attention to current and emerging directions in philological and pedagogical sciences; promoting scientific exchange and collaboration between Uzbek and international philologists; presenting research outcomes and constructive ideas relevant to both Uzbekistan and the international academic community, including innovative approaches to the teaching of philological disciplines; and familiarizing readers with contemporary trends, theories, and their practical applications developed in Uzbekistan, CIS countries, and the broader international research community. The journal also publishes original interdisciplinary studies addressing a wide range of current philological and pedagogical issues that reveal the interaction between language, culture, cognition, and communication.</p>
          <p class="mb-4"><strong>Philology Matters</strong> encourages research that integrates theories and methodologies from all traditions of philology and pedagogy to explore any aspect of language education. Areas studied at the intersection of philology and pedagogy include, but are not limited to, linguistics, literary studies, translation studies, journalism, teaching methodology, pedagogy, and psychology.</p>
          <p class="mb-4"><strong>Philology Matters</strong> is a journal focused on original research. Although articles may have practical and policy implications for education, they must be grounded in rigorous research and demonstrate a strong conceptual foundation in both analysis and discussion. The journal welcomes experimental studies, review articles, practical reports, and research projects covering various areas of philology and related disciplines, drawing upon disciplinary and interdisciplinary research traditions that reflect the principled application of qualitative, quantitative, or mixed-method paradigms. These may include, for example, applied research, ethnographic fieldwork, experimental and quasi-experimental studies, and related forms of scholarly inquiry. Articles submitted to the journal should be relevant and accessible to an international readership.</p>
          <p class="mb-0">Articles addressing all aspects of philology and pedagogical sciences may focus on any country, society, educational context, or language of the world. This includes studies related to first and second language teaching, immersion education, content-based language instruction, bilingualism/multilingualism, and learning environments. However, language and educational competence are not limited solely to contemporary foreign language education (such as modern foreign languages or English as a foreign language).</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Double-Blind Peer Review Policy</h4>
          <p class="mb-4">All research articles submitted to this journal undergo rigorous evaluation through an initial editorial screening followed by a double-blind peer review process.</p>
          <p class="mb-0">For instructions on how to submit your manuscript, please read <a href="/page/author_instructions" class="text-fmmain hover:underline">Guidelines for Authors</a>.</p>
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
          <h4 class="text-lg font-semibold mb-3">Цели и сфера деятельности</h4>
          <p class="mb-4">Электронный научно-методический журнал «Вопросы филологии» поддерживает публикацию результатов исследований, проводимых во всем мире, которые способствуют развитию знаний, теории и методологии на стыке филологии (10.00.00) и педагогики (13.00.00). Журнал уделяет особое внимание роли языка и другим филологическим вопросам в контексте педагогических задач, связанных с изучением, преподаванием и освоением первого (родного), второго и иностранных языков в мире.</p>
          <p class="mb-4">Журнал публикует исследования, направленные на предоставление научному сообществу возможностей для распространения результатов оригинальных исследований; привлечение внимания к актуальным и новым направлениям в филологических и педагогических науках; содействие научному обмену и сотрудничеству между узбекскими и зарубежными филологами; представление результатов исследований и конструктивных идей, актуальных как для Узбекистана, так и для международного научного сообщества, включая инновационные подходы к преподаванию филологических дисциплин; а также ознакомление читателей с современными тенденциями, теориями и их практическим применением, разработанными в Узбекистане, странах СНГ и более широком международном научном сообществе. Журнал также публикует оригинальные междисциплинарные исследования, посвященные широкому спектру актуальных филологических и педагогических вопросов, раскрывающих взаимодействие между языком, культурой, познанием и коммуникацией.</p>
          <p class="mb-4"><strong>«Вопросы филологии»</strong> поощряет исследования, интегрирующие теории и методологии всех традиций филологии и педагогики для изучения любых аспектов языкового образования. Области, изучаемые на стыке филологии и педагогики, включают, помимо прочего, лингвистику, литературоведение, переводоведение, журналистику, методику преподавания, педагогику и психологию.</p>
          <p class="mb-4"><strong>«Вопросы филологии»</strong> – журнал, ориентированный на оригинальные исследования. Хотя статьи могут иметь практические и политические последствия для образования, они должны быть основаны на тщательном исследовании и демонстрировать прочную концептуальную основу как в анализе, так и в дискуссии. Журнал приветствует экспериментальные исследования, обзорные статьи, практические отчеты и исследовательские проекты, охватывающие различные области филологии и смежных дисциплин, опирающиеся на дисциплинарные и междисциплинарные исследовательские традиции, отражающие принципиальное применение качественных, количественных или смешанных методологических парадигм. К ним могут относиться, например, прикладные исследования, этнографическая полевая работа, экспериментальные и квазиэкспериментальные исследования, а также связанные с ними формы научного поиска. Статьи, представляемые в журнал, должны быть актуальными и доступными для международной аудитории.</p>
          <p class="mb-0">Статьи, посвященные всем аспектам филологии и педагогических наук, могут быть сосредоточены на любой стране, обществе, образовательном контексте или языке мира. Сюда входят исследования, связанные с преподаванием первого и второго языка, погружением в языковую среду, контент-ориентированным языковым обучением, билингвизмом/мультилингвизмом и средами обучения. Однако языковая и образовательная компетентность не ограничиваются исключительно современным образованием в области иностранных языков (таких как современные иностранные языки или английский как иностранный).</p>
        </section>
        <section>
          <h4 class="text-lg font-semibold mb-3">Политика двойного слепого рецензирования</h4>
          <p class="mb-4">Все научные статьи, представленные в этот журнал, проходят тщательную оценку в ходе первоначального редакционного отбора, за которым следует процесс двойного слепого рецензирования.</p>
          <p class="mb-0">Инструкции по подаче рукописи см. в разделе <a href="/page/author_instructions" class="text-fmmain hover:underline">«Руководство для авторов»</a>.</p>
        </section>
        '''
    },
    'journal_info': {
        'title': 'Information about the journal',
        'title_uz': 'Jurnal haqida ma\'lumot',
        'title_ru': 'Информация о журнале',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">About the Journal</h4>
          <p class="mb-4">The scientific-methodological journal <strong>Philology Matters</strong>, founded by the Ministry of Higher and Secondary Specialized Education of the Republic of Uzbekistan and the Uzbekistan State World Languages University, has been published quarterly since 2002 (registered as a print publication on December 19, 2002, Certificate No. 80). The journal was re-registered on February 2, 2007 (Certificate No. 0222).</p>
          <p class="mb-4">On April 25, 2007, the journal was awarded the international ISSN certificate (ISSN: 1994-4233) by the ISSN International Centre in Paris.</p>
          <p class="mb-4">According to Resolution No. 214/2 of the Presidium of the Higher Attestation Commission under the Cabinet of Ministers of the Republic of Uzbekistan dated March 20, 2015, Philology Matters was included in the list of leading scientific journals recommended for the publication of doctoral dissertation results in the field of 10.00.00 – Philological Sciences. Furthermore, under Resolution No. 219/5 dated December 22, 2015, the journal was also recognized for publications in the field of 13.00.00 – Pedagogical Sciences.</p>
          <p class="mb-4">Since 2019, the journal has been registered with the international Digital Object Identifier (DOI) Foundation in the United States, and each published article has been assigned a unique DOI under the prefix 10.36078.</p>
          <p class="mb-4">From 2019 to the present, the journal has maintained a high impact factor according to the international database Scientific Journal Impact Factor (SJIF).</p>
          <p class="mb-4">On July 14, 2020, the journal was officially registered as an electronic journal by the Agency for Information and Mass Communications under the Administration of the President of the Republic of Uzbekistan (Certificate No. 1089) and was granted the electronic ISSN Certificate E-ISSN: 2181-1237.</p>
          <p class="mb-4">According to Resolution No. 283/7.1 of the Presidium of the Higher Attestation Commission dated July 30, 2020, articles published in English in the journal were equated with publications in international scientific journals.</p>
          <p class="mb-4">On January 25, 2021, the journal was indexed in the international scientific database Directory of Research Journals Indexing (DRJI).</p>
          <p class="mb-4">On October 22, 2021, the journal was indexed in the international scientific database Advanced Sciences Index (ASI).</p>
          <p class="mb-0">In accordance with Order No. 179 of the Rector of the Uzbekistan State World Languages University dated June 20, 2022, a mandatory procedure for the regular plagiarism screening of articles submitted to the electronic scientific-methodological journal Philology Matters was introduced through the use of anti-plagiarism software.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Indexing</h4>
          <ul class="list-disc list-inside space-y-2">
            <li>ISSN International Centre</li>
            <li>Digital Object Identifiers (DOI)</li>
            <li>Scientific Journal Impact Factor (SJIF)</li>
            <li>E-ISSN: 2181-1237</li>
            <li>Directory of Research Journals Indexing (DRJI)</li>
            <li>Advanced Sciences Index (ASI)</li>
          </ul>
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
          <p class="mb-4">Научно-методический журнал <strong>«Вопросы филологии»</strong>, основанный Министерством высшего и среднего специального образования Республики Узбекистан и Узбекским государственным университетом мировых языков, издается ежеквартально с 2002 года (зарегистрирован как печатное издание 19 декабря 2002 года, свидетельство № 80). Журнал был перерегистрирован 2 февраля 2007 года (свидетельство № 0222).</p>
          <p class="mb-4">25 апреля 2007 года журналу был присвоен международный ISSN-номер (ISSN: 1994-4233) Международным центром ISSN в Париже.</p>
          <p class="mb-4">В соответствии с Постановлением № 214/2 Президиума Высшей аттестационной комиссии при Кабинете министров Республики Узбекистан от 20 марта 2015 года журнал «Вопросы филологии» был включен в перечень ведущих научных журналов, рекомендованных для публикации результатов докторских диссертаций в области 10.00.00 – Филологические науки. Кроме того, Постановлением № 219/5 от 22 декабря 2015 года журнал был также признан для публикаций в области 13.00.00 – Педагогические науки.</p>
          <p class="mb-4">С 2019 года журнал зарегистрирован в международном Фонде цифровых идентификаторов объектов (DOI) в США, и каждой опубликованной статье присвоен уникальный DOI с префиксом 10.36078.</p>
          <p class="mb-4">С 2019 года по настоящее время журнал сохраняет высокий импакт-фактор согласно международной базе данных Scientific Journal Impact Factor (SJIF).</p>
          <p class="mb-4">14 июля 2020 года журнал был официально зарегистрирован в качестве электронного журнала Агентством по информации и массовым коммуникациям при Администрации Президента Республики Узбекистан (свидетельство № 1089) и получил электронный ISSN-сертификат E-ISSN: 2181-1237.</p>
          <p class="mb-4">В соответствии с Постановлением № 283/7.1 Президиума Высшей аттестационной комиссии от 30 июля 2020 года статьи, опубликованные на английском языке в журнале, приравнены к публикациям в международных научных журналах.</p>
          <p class="mb-4">25 января 2021 года журнал был индексирован в международной научной базе данных Directory of Research Journals Indexing (DRJI).</p>
          <p class="mb-4">22 октября 2021 года журнал был индексирован в международной научной базе данных Advanced Sciences Index (ASI).</p>
          <p class="mb-0">В соответствии с приказом ректора Узбекского государственного университета мировых языков № 179 от 20 июня 2022 года введена обязательная процедура регулярной проверки статей, представляемых в электронный научно-методический журнал «Вопросы филологии», на плагиат с использованием антиплагиатного программного обеспечения.</p>
        </section>
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">Индексирование</h4>
          <ul class="list-disc list-inside space-y-2">
            <li>Международный центр ISSN</li>
            <li>Идентификаторы цифровых объектов (DOI)</li>
            <li>Импакт-фактор научного журнала (SJIF)</li>
            <li>E-ISSN: 2181-1237</li>
            <li>Каталог индексируемых научных журналов (DRJI)</li>
            <li>Индекс передовых наук (ASI)</li>
          </ul>
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
        'title': "For O'zDJTU Researchers",
        'title_uz': 'O\'zDJTU tadqiqotchilari uchun',
        'title_ru': 'Для исследователей УзГУМЯ',
        'content': '''
        <section class="mb-8">
          <h4 class="text-lg font-semibold mb-3">For O'zDJTU Researchers</h4>
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
          <h4 class="text-lg font-semibold mb-3">O'zDJTU tadqiqotchilari uchun</h4>
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
