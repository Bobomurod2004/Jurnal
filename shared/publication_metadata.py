"""Shared publication metadata catalogs and helpers."""

PUBLICATION_METADATA_CATALOG = {
    'author_position_key': (
        {
            'key': 'trainee_teacher',
            'uz': "Stajyor-o'qituvchi",
            'ru': 'Стажёр-преподаватель',
            'en': 'Trainee Teacher',
        },
        {
            'key': 'teacher_lecturer',
            'uz': "O'qituvchi",
            'ru': 'Преподаватель',
            'en': 'Teacher / Lecturer',
        },
        {
            'key': 'senior_teacher',
            'uz': "Katta o'qituvchi",
            'ru': 'Старший преподаватель',
            'en': 'Senior Lecturer',
        },
        {
            'key': 'basic_doctoral_student',
            'uz': 'Tayanch doktorant',
            'ru': 'Базовый докторант',
            'en': 'PhD Student',
        },
        {
            'key': 'doctoral_student',
            'uz': 'Doktorant',
            'ru': 'Докторант',
            'en': 'DSc Student',
        },
        {
            'key': 'independent_researcher',
            'uz': 'Mustaqil izlanuvchi',
            'ru': 'Независимый соискатель',
            'en': 'Independent Researcher',
        },
        {
            'key': 'independent_researcher_dsc',
            'uz': 'Mustaqil izlanuvchi (DSc)',
            'ru': 'Независимый соискатель (DSc)',
            'en': 'Independent Researcher (DSc)',
        },
    ),
    'academic_title_key': (
        {
            'key': 'associate_professor_acting',
            'uz': 'Dotsent v.b.',
            'ru': 'Доцент, и.о.',
            'en': 'Associate Professor (Acting)',
        },
        {
            'key': 'associate_professor',
            'uz': 'Dotsent',
            'ru': 'Доцент',
            'en': 'Associate Professor',
        },
        {
            'key': 'professor_acting',
            'uz': 'Professor v.b.',
            'ru': 'Профессор, и.о.',
            'en': 'Professor (Acting)',
        },
        {
            'key': 'professor',
            'uz': 'Professor',
            'ru': 'Профессор',
            'en': 'Professor',
        },
    ),
    'academic_degree_key': (
        {
            'key': 'candidate_philological_sciences',
            'uz': 'Filologiya fanlari nomzodi',
            'ru': 'Кандидат филологических наук',
            'en': 'Candidate of Philological Sciences',
        },
        {
            'key': 'phd_philological_sciences',
            'uz': "Filologiya fanlari bo'yicha falsafa doktori (PhD)",
            'ru': 'Доктор философии (PhD) по филологическим наукам',
            'en': 'Doctor of Philosophy (PhD) in Philological Sciences',
        },
        {
            'key': 'doctor_philology',
            'uz': 'Filologiya fanlari doktori',
            'ru': 'Доктор наук по филологии',
            'en': 'Doctor of Sciences in Philology',
        },
        {
            'key': 'dsc_philology',
            'uz': 'Filologiya fanlari doktori (DSc)',
            'ru': 'Доктор наук (DSc) по филологии',
            'en': 'Doctor of Sciences (DSc) in Philology',
        },
        {
            'key': 'candidate_pedagogical_sciences',
            'uz': 'Pedagogika fanlari nomzodi',
            'ru': 'Кандидат педагогических наук',
            'en': 'Candidate of Pedagogical Sciences',
        },
        {
            'key': 'phd_pedagogical_sciences',
            'uz': "Pedagogika fanlari bo'yicha falsafa doktori (PhD)",
            'ru': 'Доктор философии (PhD) по педагогическим наукам',
            'en': 'Doctor of Philosophy (PhD) in Pedagogical Sciences',
        },
        {
            'key': 'doctor_pedagogy',
            'uz': 'Pedagogika fanlari doktori',
            'ru': 'Доктор наук по педагогике',
            'en': 'Doctor of Sciences in Pedagogy',
        },
        {
            'key': 'dsc_pedagogy',
            'uz': 'Pedagogika fanlari doktori (DSc)',
            'ru': 'Доктор наук (DSc) по педагогике',
            'en': 'Doctor of Sciences (DSc) in Pedagogy',
        },
        {
            'key': 'candidate_psychological_sciences',
            'uz': 'Psixologiya fanlari nomzodi',
            'ru': 'Кандидат психологических наук',
            'en': 'Candidate of Psychological Sciences',
        },
        {
            'key': 'phd_psychological_sciences',
            'uz': "Psixologiya fanlari bo'yicha falsafa doktori (PhD)",
            'ru': 'Доктор философии (PhD) по психологическим наукам',
            'en': 'Doctor of Philosophy (PhD) in Psychological Sciences',
        },
        {
            'key': 'doctor_psychology',
            'uz': 'Psixologiya fanlari doktori',
            'ru': 'Доктор наук по психологии',
            'en': 'Doctor of Sciences in Psychology',
        },
        {
            'key': 'dsc_psychology',
            'uz': 'Psixologiya fanlari doktori (DSc)',
            'ru': 'Доктор наук (DSc) по психологии',
            'en': 'Doctor of Sciences (DSc) in Psychology',
        },
        {
            'key': 'phd_language_culture',
            'uz': "Til va madaniyat bo'yicha falsafa doktori (PhD)",
            'ru': 'Доктор философии (PhD) по языку и культуре',
            'en': 'Doctor of Philosophy (PhD) in Language and Culture',
        },
        {
            'key': 'phd_linguistics',
            'uz': "Lingvistika yo'nalishi bo'yicha falsafa doktori (PhD)",
            'ru': 'Доктор философии (PhD) по лингвистике',
            'en': 'Doctor of Philosophy (PhD) in Linguistics',
        },
        {
            'key': 'phd_political_sciences',
            'uz': "Siyosiy fanlar bo'yicha falsafa doktori (PhD)",
            'ru': 'Доктор философии (PhD) по политическим наукам',
            'en': 'Doctor of Philosophy (PhD) in Political Sciences',
        },
        {
            'key': 'dsc_agriculture',
            'uz': "Qishloq xo'jalik fanlari doktori (DSc)",
            'ru': 'Доктор наук (DSc) по сельскому хозяйству',
            'en': 'Doctor of Sciences (DSc) in Agriculture',
        },
    ),
    'series_key': (
        {
            'key': 'series_masters',
            'uz': 'Seriya: Magistratura',
            'ru': 'Серия: Магистратура',
            'en': "Series: Master's Program",
        },
        {
            'key': 'series_doctoral',
            'uz': 'Seriya: Doktorantura',
            'ru': 'Серия: Докторантура',
            'en': 'Series: Doctoral Program',
        },
        {
            'key': 'series_academic_staff',
            'uz': "Seriya: Professor-o'qituvchilar",
            'ru': 'Серия: Профессорско-преподавательский состав',
            'en': 'Series: Academic Staff',
        },
        {
            'key': 'special_issue_masters',
            'uz': 'Maxsus son (magistratura)',
            'ru': 'Специальный выпуск (магистратура)',
            'en': "Special Issue (Master's Program)",
        },
        {
            'key': 'special_issue_doctoral',
            'uz': 'Maxsus son (doktorantura)',
            'ru': 'Специальный выпуск (докторантура)',
            'en': 'Special Issue (Doctoral Program)',
        },
        {
            'key': 'special_issue_academic_staff',
            'uz': "Maxsus son (professor-o'qituvchilar)",
            'ru': 'Специальный выпуск (профессорско-преподавательский состав)',
            'en': 'Special Issue (Academic Staff)',
        },
    ),
}

PUBLICATION_METADATA_FIELD_LABELS = {
    'author_position_key': {
        'uz': 'Lavozim',
        'ru': 'Должность',
        'en': 'Position',
    },
    'academic_title_key': {
        'uz': 'Ilmiy unvon',
        'ru': 'Учёное звание',
        'en': 'Academic Title',
    },
    'academic_degree_key': {
        'uz': 'Ilmiy daraja',
        'ru': 'Учёная степень',
        'en': 'Academic Degree',
    },
    'series_key': {
        'uz': 'Seriya',
        'ru': 'Серия',
        'en': 'Series',
    },
}

PUBLICATION_METADATA_COLUMN_TYPES = {
    field_name: 'text'
    for field_name in PUBLICATION_METADATA_CATALOG.keys()
}


def _normalize_lang(lang):
    normalized = str(lang or 'uz').strip().lower()
    if normalized in {'uz', 'ru', 'en'}:
        return normalized
    return 'uz'


def publication_metadata_options(field_name, lang='uz'):
    normalized_lang = _normalize_lang(lang)
    items = PUBLICATION_METADATA_CATALOG.get(field_name) or ()
    options = []
    for item in items:
        options.append({
            'key': item.get('key'),
            'label': item.get(normalized_lang) or item.get('uz') or item.get('key'),
        })
    return options


def publication_metadata_label(field_name, item_key, lang='uz'):
    if item_key in (None, ''):
        return ''
    normalized_lang = _normalize_lang(lang)
    items = PUBLICATION_METADATA_CATALOG.get(field_name) or ()
    for item in items:
        if item.get('key') == item_key:
            return item.get(normalized_lang) or item.get('uz') or item.get('key')
    return ''


def publication_metadata_field_labels(lang='uz'):
    normalized_lang = _normalize_lang(lang)
    labels = {}
    for field_name, field_labels in PUBLICATION_METADATA_FIELD_LABELS.items():
        labels[field_name] = field_labels.get(normalized_lang) or field_labels.get('uz') or field_name
    return labels


def normalize_publication_metadata_key(field_name, value):
    normalized_value = str(value or '').strip()
    if not normalized_value:
        return None
    allowed_values = {
        item.get('key')
        for item in (PUBLICATION_METADATA_CATALOG.get(field_name) or ())
    }
    if normalized_value in allowed_values:
        return normalized_value
    return None
