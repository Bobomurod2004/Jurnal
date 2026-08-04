"""Canonical submission status enum shared by mainweb and fmadmin.

Single source of truth for the 11-stage editorial pipeline, replacing the
old, drift-prone combination of `submissions.status` + `workflow_stage` +
`editor_review_status` + `rejection_origin`. The status value alone now
carries both "where in the pipeline" and "why" (e.g. `failed_technical_check`
vs `revision_required` vs `rejected` are three distinct, resubmit-aware
outcomes instead of one generic `rejected` + a separate origin flag).
"""

SUBMISSION_STATUSES = [
    'pending',
    'passed_technical_check',
    'failed_technical_check',
    'plagiarism_check',
    'antiplagiarism_failed',
    'under_review',
    'revision_required',
    'recommended',
    'payment_pending',
    'in_layout',
    'published',
    'rejected',
]

SUBMISSION_STATUS_KEYS = set(SUBMISSION_STATUSES)

SUBMISSION_STATUS_LABELS = {
    'pending': {
        'uz': "Kutilmoqda",
        'ru': "Ожидает",
        'en': "Pending",
    },
    'passed_technical_check': {
        'uz': "Texnik tekshiruvdan o'tdi",
        'ru': "Прошёл техническую проверку",
        'en': "Passed technical check",
    },
    'failed_technical_check': {
        'uz': "Texnik tekshiruvdan o'tmadi",
        'ru': "Не прошёл техническую проверку",
        'en': "Failed technical check",
    },
    'plagiarism_check': {
        'uz': "Antiplagiat tekshiruvida",
        'ru': "На проверке на плагиат",
        'en': "Under plagiarism check",
    },
    'antiplagiarism_failed': {
        'uz': "Antiplagiat tekshiruvidan o'tmadi",
        'ru': "Не прошёл проверку на плагиат",
        'en': "Failed plagiarism check",
    },
    'under_review': {
        'uz': "Taqrizda",
        'ru': "На рецензировании",
        'en': "Under review",
    },
    'revision_required': {
        'uz': "Tuzatish kutilmoqda",
        'ru': "Ожидается доработка",
        'en': "Revision required",
    },
    'recommended': {
        'uz': "Nashrga tavsiya etildi",
        'ru': "Рекомендовано к публикации",
        'en': "Recommended for publication",
    },
    'payment_pending': {
        'uz': "To'lov kutilmoqda",
        'ru': "Ожидается оплата",
        'en': "Payment pending",
    },
    'in_layout': {
        'uz': "Sahifalanmoqda",
        'ru': "Выполняется вёрстка",
        'en': "In page layout",
    },
    'published': {
        'uz': "Nashr etildi",
        'ru': "Опубликовано",
        'en': "Published",
    },
    'rejected': {
        'uz': "Rad etildi",
        'ru': "Отклонен",
        'en': "Rejected",
    },
}

# Tabler/Bootstrap badge tone (`bg-{tone}-lt`) per status.
SUBMISSION_STATUS_BADGE_TONE = {
    'pending': 'blue',
    'passed_technical_check': 'teal',
    'failed_technical_check': 'red',
    'plagiarism_check': 'purple',
    'antiplagiarism_failed': 'red',
    'under_review': 'orange',
    'revision_required': 'yellow',
    'recommended': 'indigo',
    'payment_pending': 'orange',
    'in_layout': 'cyan',
    'published': 'green',
    'rejected': 'red',
}

# Chart.js does not understand Tabler's badge tone names, therefore the
# dashboard receives these matching hex colours explicitly.  Keeping the
# mapping alongside the badge tones prevents terminal statuses from appearing
# with a contradictory colour in the dashboard: published is green and
# rejected is red everywhere.
SUBMISSION_STATUS_CHART_COLOR = {
    'pending': '#2563EB',
    'passed_technical_check': '#0F766E',
    'failed_technical_check': '#EF4444',
    'plagiarism_check': '#8B5CF6',
    'antiplagiarism_failed': '#EF4444',
    'under_review': '#F59E0B',
    'revision_required': '#EAB308',
    'recommended': '#6366F1',
    'payment_pending': '#F59E0B',
    'in_layout': '#06B6D4',
    'published': '#22C55E',
    'rejected': '#EF4444',
}

# Statuses from which the author is allowed to edit and resubmit the same
# submission. `rejected` is deliberately excluded -- it is final.
RESUBMITTABLE_STATUSES = {'failed_technical_check', 'revision_required', 'antiplagiarism_failed'}

# Statuses past which no further pipeline transition happens.
TERMINAL_STATUSES = {'published', 'rejected'}

# Entering any of these statuses requires the anti-plagiarism file to
# already be uploaded and checked (mirrors the pre-existing gate that used
# to be keyed off `workflow_stage`).
STATUSES_REQUIRING_ANTIPLAGIARISM_FILE = {
    'under_review', 'revision_required', 'recommended',
    'payment_pending', 'in_layout', 'published',
}

# Setting the status to any of these requires a non-empty explanatory note,
# since the author is being told something went wrong / needs action.
STATUSES_REQUIRING_NOTE = {
    'failed_technical_check', 'revision_required', 'antiplagiarism_failed', 'rejected',
}

# Only these transitions warrant an email ping (in addition to the in-app
# notification, which fires for every status change). Keeps the author's
# inbox to the moments that actually require attention or are worth
# celebrating, instead of one email per internal pipeline step.
EMAIL_NOTIFIED_STATUSES = {
    'failed_technical_check', 'revision_required', 'antiplagiarism_failed',
    'payment_pending', 'published', 'rejected',
}

# Outcome of the anti-plagiarism check itself (submissions.anti_plagiarism_status),
# separate from the pipeline `status` -- a file can be uploaded (by the author
# OR an admin, see anti_plagiarism_uploaded_by_role) without yet being marked
# passed or failed.
ANTIPLAGIARISM_STATUSES = ('pending', 'passed', 'failed')

ANTIPLAGIARISM_STATUS_LABELS = {
    'pending': {
        'uz': "Tekshirilmoqda",
        'ru': "На проверке",
        'en': "Pending review",
    },
    'passed': {
        'uz': "O'tdi",
        'ru': "Пройдена",
        'en': "Passed",
    },
    'failed': {
        'uz': "O'tmadi",
        'ru': "Не пройдена",
        'en': "Failed",
    },
}

ANTIPLAGIARISM_STATUS_BADGE_TONE = {
    'pending': 'yellow',
    'passed': 'green',
    'failed': 'red',
}


def _normalize_lang(lang):
    normalized = str(lang or 'uz').strip().lower()
    if normalized in {'uz', 'ru', 'en'}:
        return normalized
    return 'uz'


def submission_status_label(status, lang='uz'):
    normalized_lang = _normalize_lang(lang)
    labels = SUBMISSION_STATUS_LABELS.get(status)
    if not labels:
        return status or ''
    return labels.get(normalized_lang) or labels.get('uz') or status


def is_resubmittable(status):
    return status in RESUBMITTABLE_STATUSES


def is_terminal(status):
    return status in TERMINAL_STATUSES


def requires_antiplagiarism_file(status):
    return status in STATUSES_REQUIRING_ANTIPLAGIARISM_FILE


def requires_note(status):
    return status in STATUSES_REQUIRING_NOTE


def should_email_on_status(status):
    return status in EMAIL_NOTIFIED_STATUSES


def anti_plagiarism_status_label(anti_plagiarism_status, lang='uz'):
    normalized_lang = _normalize_lang(lang)
    labels = ANTIPLAGIARISM_STATUS_LABELS.get(anti_plagiarism_status)
    if not labels:
        return anti_plagiarism_status or ''
    return labels.get(normalized_lang) or labels.get('uz') or anti_plagiarism_status
