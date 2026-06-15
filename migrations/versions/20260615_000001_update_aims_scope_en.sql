-- Update English content for the aims_scope page.
-- Uzbek and Russian page content is left unchanged.

UPDATE pages
SET
    title = 'Aims and Scope',
    content = $AIMS_EN$
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
$AIMS_EN$,
    last_update = EXTRACT(EPOCH FROM NOW())::bigint
WHERE alias = 'aims_scope';
