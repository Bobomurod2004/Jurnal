# flake8: noqa
import time
from flask import session

# Global DB connector instance
dbc = None

# Translations cache
_translations_cache = {}
_cache_timestamp = 0
_cache_ttl = 300  # 5 minutes
SUPPORTED_LANGUAGES = {'uz', 'ru', 'en'}


def _current_language():
    """Return the session language, consistently defaulting to Uzbek."""
    language = str(session.get('language') or 'uz').strip().lower()
    return language if language in SUPPORTED_LANGUAGES else 'uz'

STATIC_TRANSLATIONS = {
    'uz': {
        'admin_authors_duplicate_warning': "Dublikat akkauntlar aniqlandi",
        'admin_authors_duplicate_hint': "Bu muallif bilan bir xil email yoki ORCID ga ega boshqa foydalanuvchilar mavjud. Birlashtirish uchun tugmani bosing.",
        'admin_authors_merge_confirm': "Akkauntlarni birlashtirmoqchimisiz? Bu amal qaytarib bo'lmaydi.",
        'admin_authors_merge_btn': "Birlashtirish",
        'admin_authors_merge_no_primary': "Avval asosiy foydalanuvchini bog'lang",
        'admin_authors_duplicate_badge_title': "Dublikat akkaunt mavjud",
        'admin_authors_department_placeholder': "Masalan: Fizika kafedrasi",
        'admin_payments_title': "To'lovlar",
        'admin_title_edit_payment': "To'lovni tahrirlash",
        'admin_label_filters': "Filtrlar",
        'admin_label_status': "Holat",
        'admin_label_all_statuses': "Barcha holatlar",
        'admin_label_status_pending': "Kutilmoqda",
        'admin_label_status_paid': "To'lov qilingan",
        'admin_label_status_rejected': "Rad etilgan",
        'admin_label_user': "Foydalanuvchi",
        'admin_label_amount': "To'lov summasi",
        'admin_label_created_at': "Yaratilgan sana",
        'admin_label_updated_at': "Yangilangan sana",
        'admin_label_file': "Fayl",
        'admin_label_actions': "Amallar",
        'admin_label_current_file': "Joriy fayl",
        'admin_label_comment': "Izoh",
        'admin_btn_apply': "Qo'llash",
        'admin_btn_reset': "Tozalash",
        'admin_btn_edit': "Tahrirlash",
        'admin_btn_save_changes': "Saqlash",
        'admin_btn_cancel': "Bekor qilish",
        'admin_btn_view': "Ko'rish",
        'admin_btn_view_current_file': "Joriy faylni ko'rish",
        'admin_msg_no_file': "Fayl yuklanmagan",
        'admin_msg_file_not_uploaded': "Fayl yuklanmagan",
        'admin_msg_error_saving': "Saqlashda xatolik",
        'admin_msg_unknown_error': "Noma'lum xatolik",
        'admin_msg_request_error': "So'rovda xatolik",
        'admin_pagination_showing': "Ko'rsatilmoqda",
        'admin_pagination_of': "dan",
        'admin_pagination_entries': "ta yozuv",
        'admin_label_issue_toc_file': "Mundarija fayli",
        'admin_btn_download_issue_toc': "Mundarijani yuklab olish",
        'admin_hint_issue_toc_file': "Ruxsat etilgan formatlar: PDF, DOC, DOCX",
        'admin_scholar_abstract_hint': "Google Scholar uchun to'liq inglizcha annotatsiya majburiy.",
        'admin_scholar_pdf_hint': "Ochiq kirish maqolasi uchun kamida bitta PDF majburiy.",
        'admin_login_brand_subtitle': "Filologiya masalalari jurnali",
        'admin_login_headline_line_1': "Boshqaruv",
        'admin_login_headline_line_2': "markazi",
        'admin_login_tagline': "Maqolalar, sonlar va tahririyat jarayonini bir joydan boshqaring.",
        'admin_login_form_subtitle': "Davom etish uchun ma'lumotlaringizni kiriting",
        'admin_login_language_label': "Tilni tanlang",
        'admin_login_close_alert': "Yopish",
        'admin_login_hide_password': "Parolni yashirish",
        'admin_login_footer_note': "Faqat vakolatli xodimlar uchun. Kirish urinishlari qayd etiladi.",
        'admin_login_support_empty': "Yordam Telegram kontaktlari sozlanmagan.",
        'admin_login_support_admin_title': "Login uchun yordam kontaktlari",
        'admin_login_support_admin_description': "Kirishda muammo bo'lsa ko'rsatiladigan Telegram kontaktlarini kiriting.",
        'admin_login_support_add': "Kontakt qo'shish",
        'admin_login_support_empty_admin': "Hali yordam kontakti qo'shilmagan.",
        'admin_login_support_label': "Nomi",
        'admin_login_support_username': "Telegram username",
        'admin_login_support_remove': "O'chirish",
        'admin_users_assign_editor_title': "Foydalanuvchilardan muharrir tayinlash",
        'admin_users_assign_editor_description': "Foydalanuvchilarni ko'rib, mos hisobga muharrir rolini bering.",
        'admin_users_directory_description': "Barcha ro'yxatdan o'tgan foydalanuvchilarni ko'rish va boshqarish.",
        'admin_users_summary_total': "Jami",
        'admin_users_summary_active': "Faol",
        'admin_users_summary_staff': "Xodimlar",
        'admin_users_filter_all': "Barchasi",
        'admin_users_filter_role_all': "Barcha rollar",
        'admin_users_table_user': "Foydalanuvchi",
        'admin_users_status_active': "Faol",
        'admin_users_status_hidden': "Yashirilgan",
        'admin_users_role_author': "Muallif",
        'admin_role_user': "Muallif",
        'admin_role_superadmin': "Super Admin",
        'admin_users_primary_role': "Asosiy rol",
        'admin_users_assigned_admin': "Admin",
        'admin_users_unassigned': "Biriktirilmagan",
        'admin_users_open_user': "Foydalanuvchini ochish",
        'admin_users_no_results': "Mos foydalanuvchilar topilmadi.",
        'admin_users_tab_details': "Ma'lumotlar",
        'admin_users_tab_activity': "360° va faoliyat",
        'admin_users_section_personal': "Shaxsiy ma'lumotlar",
        'admin_users_section_access': "Rol va ruxsatlar",
        'admin_users_section_account': "Hisob sozlamalari",
        'admin_users_section_security': "Xavfsizlik",
        'admin_users_section_subscription': "Tarif va obuna",
        'admin_users_section_account_activity': "Hisob tarixi",
        'admin_users_access_hint': "Asosiy rol va qo'shimcha imkoniyatlarni boshqaring.",
        'admin_users_assigned_roles': "Berilgan rollar",
        'admin_users_role_help': "Asosiy rol dashboard va tizimdagi ustuvor xatti-harakatni belgilaydi.",
        'admin_users_admin_tracks': "Admin yo'nalishlari",
        'admin_users_admin_tracks_hint': "Belgilangan yo'nalishdagi maqolalar shu adminga tushadi.",
        'admin_users_editor_admin': "Biriktirilgan admin",
        'admin_users_editor_admin_hint': "Muharrir qaysi admin bilan ishlashini belgilang.",
        'admin_users_security_hint': "Parol faqat almashtirish kerak bo'lganda saqlanadi.",
        'admin_users_password': "Parol",
        'admin_users_password_hint': "Almashtirish uchun kiriting",
        'admin_users_password_confirm': "Parolni tasdiqlash",
        'admin_users_password_confirm_hint': "Parolni qayta kiriting",
        'admin_users_no_activity': "Faoliyat yozuvlari topilmadi.",
        'admin_feedback_success_title': "Muvaffaqiyatli saqlandi",
        'admin_feedback_error_title': "Amal bajarilmadi",
        'admin_feedback_warning_title': "E'tibor bering",
        'admin_feedback_info_title': "Ma'lumot",
        'admin_feedback_error_reason': "Sabab",
        'admin_feedback_close': "Yopish",
        'admin_feedback_saving_title': "Saqlanmoqda...",
        'admin_feedback_saving_hint': "O'zgarishlar qayta ishlanmoqda.",
    },
    'ru': {
        'admin_authors_duplicate_warning': "Обнаружены дублирующиеся аккаунты",
        'admin_authors_duplicate_hint': "Найдены другие пользователи с тем же email или ORCID. Нажмите кнопку для объединения.",
        'admin_authors_merge_confirm': "Объединить аккаунты? Это действие необратимо.",
        'admin_authors_merge_btn': "Объединить",
        'admin_authors_merge_no_primary': "Сначала привяжите основного пользователя",
        'admin_authors_duplicate_badge_title': "Есть дублирующий аккаунт",
        'admin_authors_department_placeholder': "Например: Кафедра физики",
        'admin_payments_title': "Платежи",
        'admin_title_edit_payment': "Редактировать платеж",
        'admin_label_filters': "Фильтры",
        'admin_label_status': "Статус",
        'admin_label_all_statuses': "Все статусы",
        'admin_label_status_pending': "Ожидается",
        'admin_label_status_paid': "Оплачено",
        'admin_label_status_rejected': "Отклонено",
        'admin_label_user': "Пользователь",
        'admin_label_amount': "Сумма",
        'admin_label_created_at': "Создано",
        'admin_label_updated_at': "Обновлено",
        'admin_label_file': "Файл",
        'admin_label_actions': "Действия",
        'admin_label_current_file': "Текущий файл",
        'admin_label_comment': "Комментарий",
        'admin_btn_apply': "Применить",
        'admin_btn_reset': "Сбросить",
        'admin_btn_edit': "Редактировать",
        'admin_btn_save_changes': "Сохранить",
        'admin_btn_cancel': "Отмена",
        'admin_btn_view': "Просмотр",
        'admin_btn_view_current_file': "Просмотреть файл",
        'admin_msg_no_file': "Файл не загружен",
        'admin_msg_file_not_uploaded': "Файл не загружен",
        'admin_msg_error_saving': "Ошибка сохранения",
        'admin_msg_unknown_error': "Неизвестная ошибка",
        'admin_msg_request_error': "Ошибка запроса",
        'admin_pagination_showing': "Показано",
        'admin_pagination_of': "из",
        'admin_pagination_entries': "записей",
        'admin_label_issue_toc_file': "Файл содержания выпуска",
        'admin_btn_download_issue_toc': "Скачать содержание",
        'admin_hint_issue_toc_file': "Разрешённые форматы: PDF, DOC, DOCX",
        'admin_scholar_abstract_hint': "Для Google Scholar обязательна полная аннотация на английском языке.",
        'admin_scholar_pdf_hint': "Для статьи с открытым доступом требуется хотя бы один PDF-файл.",
        'admin_login_brand_subtitle': "Журнал филологических вопросов",
        'admin_login_headline_line_1': "Центр",
        'admin_login_headline_line_2': "управления",
        'admin_login_tagline': "Управляйте статьями, выпусками и редакционными процессами из одного места.",
        'admin_login_form_subtitle': "Введите данные, чтобы продолжить",
        'admin_login_language_label': "Выберите язык",
        'admin_login_close_alert': "Закрыть",
        'admin_login_hide_password': "Скрыть пароль",
        'admin_login_footer_note': "Только для уполномоченных сотрудников. Попытки входа регистрируются.",
        'admin_login_support_empty': "Контакты Telegram для помощи пока не настроены.",
        'admin_login_support_admin_title': "Контакты помощи для входа",
        'admin_login_support_admin_description': "Укажите Telegram-контакты, которые будут показаны при проблемах со входом.",
        'admin_login_support_add': "Добавить контакт",
        'admin_login_support_empty_admin': "Контакты помощи ещё не добавлены.",
        'admin_login_support_label': "Название",
        'admin_login_support_username': "Имя пользователя Telegram",
        'admin_login_support_remove': "Удалить",
        'admin_users_assign_editor_title': "Назначение редактора из пользователей",
        'admin_users_assign_editor_description': "Просмотрите пользователей и назначьте подходящей учётной записи роль редактора.",
        'admin_users_directory_description': "Просмотр и управление всеми зарегистрированными пользователями.",
        'admin_users_summary_total': "Всего",
        'admin_users_summary_active': "Активные",
        'admin_users_summary_staff': "Сотрудники",
        'admin_users_filter_all': "Все",
        'admin_users_filter_role_all': "Все роли",
        'admin_users_table_user': "Пользователь",
        'admin_users_status_active': "Активен",
        'admin_users_status_hidden': "Скрыт",
        'admin_users_role_author': "Автор",
        'admin_role_user': "Автор",
        'admin_role_superadmin': "Супер Админ",
        'admin_users_primary_role': "Основная роль",
        'admin_users_assigned_admin': "Администратор",
        'admin_users_unassigned': "Не назначен",
        'admin_users_open_user': "Открыть пользователя",
        'admin_users_no_results': "Подходящие пользователи не найдены.",
        'admin_users_tab_details': "Данные",
        'admin_users_tab_activity': "360° и активность",
        'admin_users_section_personal': "Личные данные",
        'admin_users_section_access': "Роли и разрешения",
        'admin_users_section_account': "Настройки учётной записи",
        'admin_users_section_security': "Безопасность",
        'admin_users_section_subscription': "Тариф и подписка",
        'admin_users_section_account_activity': "История учётной записи",
        'admin_users_access_hint': "Управляйте основной ролью и дополнительными возможностями.",
        'admin_users_assigned_roles': "Назначенные роли",
        'admin_users_role_help': "Основная роль определяет панель управления и приоритетное поведение в системе.",
        'admin_users_admin_tracks': "Направления администратора",
        'admin_users_admin_tracks_hint': "Заявки выбранных направлений поступают этому администратору.",
        'admin_users_editor_admin': "Назначенный администратор",
        'admin_users_editor_admin_hint': "Укажите администратора, с которым работает редактор.",
        'admin_users_security_hint': "Пароль сохраняется только при необходимости его изменить.",
        'admin_users_password': "Пароль",
        'admin_users_password_hint': "Введите для изменения",
        'admin_users_password_confirm': "Подтвердите пароль",
        'admin_users_password_confirm_hint': "Введите пароль повторно",
        'admin_users_no_activity': "Записи активности не найдены.",
        'admin_feedback_success_title': "Успешно сохранено",
        'admin_feedback_error_title': "Не удалось выполнить действие",
        'admin_feedback_warning_title': "Обратите внимание",
        'admin_feedback_info_title': "Информация",
        'admin_feedback_error_reason': "Причина",
        'admin_feedback_close': "Закрыть",
        'admin_feedback_saving_title': "Сохранение...",
        'admin_feedback_saving_hint': "Изменения обрабатываются.",
    },
    'en': {
        'admin_authors_duplicate_warning': "Duplicate accounts detected",
        'admin_authors_duplicate_hint': "Other users with the same email or ORCID were found. Click merge to consolidate them.",
        'admin_authors_merge_confirm': "Merge accounts? This action cannot be undone.",
        'admin_authors_merge_btn': "Merge",
        'admin_authors_merge_no_primary': "Link a primary user first",
        'admin_authors_duplicate_badge_title': "Has duplicate account",
        'admin_authors_department_placeholder': "E.g. Department of Physics",
        'admin_payments_title': "Payments",
        'admin_title_edit_payment': "Edit payment",
        'admin_label_filters': "Filters",
        'admin_label_status': "Status",
        'admin_label_all_statuses': "All statuses",
        'admin_label_status_pending': "Pending",
        'admin_label_status_paid': "Paid",
        'admin_label_status_rejected': "Rejected",
        'admin_label_user': "User",
        'admin_label_amount': "Amount",
        'admin_label_created_at': "Created at",
        'admin_label_updated_at': "Updated at",
        'admin_label_file': "File",
        'admin_label_actions': "Actions",
        'admin_label_current_file': "Current file",
        'admin_label_comment': "Comment",
        'admin_btn_apply': "Apply",
        'admin_btn_reset': "Reset",
        'admin_btn_edit': "Edit",
        'admin_btn_save_changes': "Save changes",
        'admin_btn_cancel': "Cancel",
        'admin_btn_view': "View",
        'admin_btn_view_current_file': "View file",
        'admin_msg_no_file': "No file",
        'admin_msg_file_not_uploaded': "File not uploaded",
        'admin_msg_error_saving': "Save error",
        'admin_msg_unknown_error': "Unknown error",
        'admin_msg_request_error': "Request error",
        'admin_pagination_showing': "Showing",
        'admin_pagination_of': "of",
        'admin_pagination_entries': "entries",
        'admin_label_issue_toc_file': "Issue table of contents file",
        'admin_btn_download_issue_toc': "Download table of contents",
        'admin_hint_issue_toc_file': "Allowed formats: PDF, DOC, DOCX",
        'admin_scholar_abstract_hint': "A complete English abstract is required for Google Scholar.",
        'admin_scholar_pdf_hint': "At least one PDF is required for an open-access article.",
        'admin_login_brand_subtitle': "Philology Matters journal",
        'admin_login_headline_line_1': "Control",
        'admin_login_headline_line_2': "center",
        'admin_login_tagline': "Manage articles, issues, and editorial workflows from one place.",
        'admin_login_form_subtitle': "Enter your details to continue",
        'admin_login_language_label': "Select language",
        'admin_login_close_alert': "Close",
        'admin_login_hide_password': "Hide password",
        'admin_login_footer_note': "For authorized staff only. Login attempts are logged.",
        'admin_login_support_empty': "Support Telegram contacts are not configured yet.",
        'admin_login_support_admin_title': "Login support contacts",
        'admin_login_support_admin_description': "Add Telegram contacts to show when someone has trouble signing in.",
        'admin_login_support_add': "Add contact",
        'admin_login_support_empty_admin': "No support contacts have been added yet.",
        'admin_login_support_label': "Label",
        'admin_login_support_username': "Telegram username",
        'admin_login_support_remove': "Remove",
        'admin_users_assign_editor_title': "Assign editor from users",
        'admin_users_assign_editor_description': "Review users and assign the editor role to the appropriate account.",
        'admin_users_directory_description': "View and manage all registered users.",
        'admin_users_summary_total': "Total",
        'admin_users_summary_active': "Active",
        'admin_users_summary_staff': "Staff",
        'admin_users_filter_all': "All",
        'admin_users_filter_role_all': "All roles",
        'admin_users_table_user': "User",
        'admin_users_status_active': "Active",
        'admin_users_status_hidden': "Hidden",
        'admin_users_role_author': "Author",
        'admin_role_user': "Author",
        'admin_role_superadmin': "Super Admin",
        'admin_users_primary_role': "Primary role",
        'admin_users_assigned_admin': "Admin",
        'admin_users_unassigned': "Unassigned",
        'admin_users_open_user': "Open user",
        'admin_users_no_results': "No matching users found.",
        'admin_users_tab_details': "Details",
        'admin_users_tab_activity': "360° & activity",
        'admin_users_section_personal': "Personal details",
        'admin_users_section_access': "Roles & permissions",
        'admin_users_section_account': "Account settings",
        'admin_users_section_security': "Security",
        'admin_users_section_subscription': "Tariff & subscription",
        'admin_users_section_account_activity': "Account history",
        'admin_users_access_hint': "Manage the primary role and additional capabilities.",
        'admin_users_assigned_roles': "Assigned roles",
        'admin_users_role_help': "The primary role determines dashboard and priority system behaviour.",
        'admin_users_admin_tracks': "Admin tracks",
        'admin_users_admin_tracks_hint': "Submissions in the selected tracks go to this admin.",
        'admin_users_editor_admin': "Assigned admin",
        'admin_users_editor_admin_hint': "Choose the admin this editor works with.",
        'admin_users_security_hint': "The password is saved only when it needs to be changed.",
        'admin_users_password': "Password",
        'admin_users_password_hint': "Enter to change",
        'admin_users_password_confirm': "Confirm password",
        'admin_users_password_confirm_hint': "Re-enter password",
        'admin_users_no_activity': "No activity records found.",
        'admin_feedback_success_title': "Saved successfully",
        'admin_feedback_error_title': "Action could not be completed",
        'admin_feedback_warning_title': "Please note",
        'admin_feedback_info_title': "Information",
        'admin_feedback_error_reason': "Reason",
        'admin_feedback_close': "Close",
        'admin_feedback_saving_title': "Saving...",
        'admin_feedback_saving_hint': "Your changes are being processed.",
    },
}

def init_translations(db_connector):
    """Initialize the translation module with a database connector."""
    global dbc
    dbc = db_connector


def _translation_is_usable(value, key):
    if value is None:
        return False

    normalized = str(value).strip()
    if not normalized:
        return False

    lowered = normalized.lower()
    placeholders = {
        str(key).strip().lower(),
        str(key).replace('_', ' ').strip().lower(),
        str(key).replace('_', '-').strip().lower(),
    }
    return lowered not in placeholders


def _humanize_translation_key(key):
    acronyms = {
        'api': 'API',
        'doi': 'DOI',
        'eissn': 'E-ISSN',
        'en': 'EN',
        'id': 'ID',
        'issn': 'ISSN',
        'orcid': 'ORCID',
        'pdf': 'PDF',
        'ru': 'RU',
        'uz': 'UZ',
    }
    tokens = [token for token in str(key).split('_') if token]
    if tokens and tokens[0].lower() == 'admin':
        tokens = tokens[1:]
    pretty = [acronyms.get(token.lower(), token.capitalize()) for token in tokens]
    return ' '.join(pretty) if pretty else str(key)

def _load_translations_from_db():
    """Loads translations from the database with caching."""
    global _translations_cache, _cache_timestamp

    current_time = time.time()

    # Check if cache needs update
    if current_time - _cache_timestamp > _cache_ttl or not _translations_cache:
        try:
            if not dbc:
                return _get_fallback_translations()

            # Load all translations from DB
            translations = dbc.translations.all().exec()

            # Organize by language
            _translations_cache = {
                'en': {},
                'ru': {},
                'uz': {}
            }

            for trans in translations:
                alias = trans['alias']
                _translations_cache['en'][alias] = trans.get('content', '')
                _translations_cache['ru'][alias] = trans.get('content_ru', '')
                _translations_cache['uz'][alias] = trans.get('content_uz', '')

            _cache_timestamp = current_time

        except Exception as e:
            print(f"Error loading translations from DB: {e}")
            if not _translations_cache:
                _translations_cache = _get_fallback_translations()

    return _translations_cache

def _get_fallback_translations():
    """Returns fallback translations."""
    return {
        'en': {'admin_home': 'Home', 'admin_users': 'Users'},
        'ru': {'admin_home': 'Главная', 'admin_users': 'Пользователи'},
        'uz': {'admin_home': 'Bosh sahifa', 'admin_users': 'Foydalanuvchilar'}
    }

def translate(data):
    """Translates object fields based on current language."""
    current_lang = _current_language()
    if current_lang == 'en':
        return data

    fields = list(data.keys())
    keys_to_delete = []

    for field in fields:
        if field.endswith('_uz') or field.endswith('_ru'):
            keys_to_delete.append(field)
            continue

        if current_lang == 'uz':
            if f'{field}_uz' in data:
                localized_value = data.get(f'{field}_uz')
                data[field] = '' if localized_value is None else localized_value
                keys_to_delete.append(f'{field}_uz')
        elif current_lang == 'ru':
            if f'{field}_ru' in data:
                localized_value = data.get(f'{field}_ru')
                data[field] = '' if localized_value is None else localized_value
                keys_to_delete.append(f'{field}_ru')

        if current_lang != 'uz' and f'{field}_uz' in data:
            keys_to_delete.append(f'{field}_uz')
        if current_lang != 'ru' and f'{field}_ru' in data:
            keys_to_delete.append(f'{field}_ru')

    for key in keys_to_delete:
        if key in data:
            del data[key]

    return data

def t(key):
    """Returns translation for a key in the current language."""
    current_lang = _current_language()

    translations_cache = _load_translations_from_db()

    if current_lang in translations_cache and key in translations_cache[current_lang]:
        val = translations_cache[current_lang][key]
        if _translation_is_usable(val, key):
            return val

    static_lang = STATIC_TRANSLATIONS.get(current_lang, {})
    if key in static_lang and _translation_is_usable(static_lang[key], key):
        return static_lang[key]

    # Missing values should not silently switch an English/Uzbek screen to
    # Russian. Prefer the canonical English text, then the other languages.
    for fallback_lang in ('en', 'uz', 'ru'):
        if fallback_lang == current_lang:
            continue
        translated = translations_cache.get(fallback_lang, {}).get(key)
        if _translation_is_usable(translated, key):
            return translated
        static_translation = STATIC_TRANSLATIONS.get(fallback_lang, {}).get(key)
        if _translation_is_usable(static_translation, key):
            return static_translation
       
    # Auto-add missing keys
    if dbc and key not in translations_cache.get('en', {}):
        try:
            dbc.translations.add(
                alias=key,
                content=key, # Default EN
                content_ru=key, # Default RU
                content_uz=key, # Default UZ
                created_at=int(time.time())
            ).exec()
            
            # Update cache locally to avoid immediate re-fetch
            if 'en' not in translations_cache: translations_cache['en'] = {}
            if 'ru' not in translations_cache: translations_cache['ru'] = {}
            if 'uz' not in translations_cache: translations_cache['uz'] = {}
            translations_cache['en'][key] = key
            translations_cache['ru'][key] = key
            translations_cache['uz'][key] = key
            
            print(f"Added new translation alias: {key}")
        except Exception as e:
            print(f"Error adding translation alias {key}: {e}")

    return _humanize_translation_key(key)

def clear_translations_cache():
    global _translations_cache, _cache_timestamp
    _translations_cache = {}
    _cache_timestamp = 0
