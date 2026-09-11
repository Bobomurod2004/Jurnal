"""Special-issue metadata, documents and presentation shared by both apps."""
import datetime
import json
import os
import re
import uuid
import zipfile
from pathlib import Path

from psycopg2.errors import UndefinedTable

SPECIAL_CATEGORIES = ('special_masters', 'special_phd', 'special_teacher')
LANGUAGES = {'uz': "O'zbekcha", 'ru': 'Русский', 'en': 'English'}
LOCALIZED_FIELDS = ('description', 'organizer', 'venue', 'publication_languages')
DOCUMENT_KINDS = ('letter', 'program', 'template', 'committee', 'other')
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
MAX_DOCUMENTS = 30


def is_special_issue(issue):
    return str((issue or {}).get('category') or '').strip().lower() in SPECIAL_CATEGORIES


def decode_details(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            value = {}
    return value if isinstance(value, dict) else {}


def documents_from(data):
    documents = decode_details(data).get('documents')
    if not isinstance(documents, list):
        return []
    return [doc for doc in documents if isinstance(doc, dict) and doc.get('id')]


def load_details(connection, issue_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT data FROM special_issue_details WHERE issue_id = %s', (issue_id,))
            row = cursor.fetchone()
        connection.commit()
        return decode_details(row[0]) if row else {}
    except UndefinedTable:
        # Older deployments can still render all issues before the migration.
        connection.rollback()
        return {}


def ensure_schema(connection, allow_create=False):
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('public.special_issue_details')")
        exists = bool(cursor.fetchone()[0])
    connection.commit()
    if exists:
        return True
    if not allow_create:
        return False
    migration = Path(__file__).resolve().parents[1] / 'migrations/versions/20260911_000001_add_special_issue_details.sql'
    try:
        with connection.cursor() as cursor:
            cursor.execute(migration.read_text())
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return True


def metadata_from_form(form):
    data = {}
    for field in LOCALIZED_FIELDS:
        data[field] = {lang: str(form.get(f'special_{field}_{lang}') or '').strip() for lang in LANGUAGES}
        limit = 12000 if field == 'description' else 500
        if any(len(text) > limit for text in data[field].values()):
            raise ValueError(f'Matn juda uzun: {field} (maksimal {limit} belgi).')
    event_date = str(form.get('special_event_date') or '').strip()
    if event_date:
        try:
            datetime.date.fromisoformat(event_date)
        except ValueError:
            raise ValueError("Tadbir sanasi noto'g'ri.") from None
    data['event_date'] = event_date
    return data


def save_metadata(connection, issue_id, metadata):
    # Merge metadata atomically; concurrent document changes remain intact.
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO special_issue_details (issue_id, data) VALUES (%s, %s::jsonb)
                ON CONFLICT (issue_id) DO UPDATE
                SET data = special_issue_details.data || EXCLUDED.data
            ''', (issue_id, json.dumps(metadata)))
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def edit_documents(connection, issue_id, update):
    """Serialize uploads/removals so they cannot overwrite each other."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO special_issue_details (issue_id) VALUES (%s) ON CONFLICT DO NOTHING', (issue_id,))
            cursor.execute('SELECT data FROM special_issue_details WHERE issue_id = %s FOR UPDATE', (issue_id,))
            data = decode_details(cursor.fetchone()[0])
            documents = documents_from(data)
            result = update(documents)
            data['documents'] = documents
            cursor.execute('UPDATE special_issue_details SET data = %s::jsonb WHERE issue_id = %s', (json.dumps(data), issue_id))
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise


def document_path(root, stored_path):
    """Only this feature's generated filenames may be served or deleted."""
    if not isinstance(stored_path, str) or not re.fullmatch(r'/static/uploads/special_issues/[0-9a-f]{32}\.(pdf|doc|docx)', stored_path):
        return None
    directory = os.path.realpath(os.path.join(root, 'static/uploads/special_issues'))
    path = os.path.realpath(os.path.join(root, stored_path.lstrip('/')))
    return path if os.path.dirname(path) == directory else None


def save_document(root, upload):
    filename = str(upload.filename or '').replace('\\', '/').rsplit('/', 1)[-1]
    suffix = os.path.splitext(filename)[1].lower()
    if suffix not in ('.pdf', '.doc', '.docx'):
        raise ValueError('Faqat PDF, DOC yoki DOCX fayl yuklang.')
    stream = upload.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if not size or size > MAX_DOCUMENT_BYTES:
        raise ValueError("Fayl bo'sh yoki hajmi 10 MB dan katta.")
    signature = stream.read(8)
    stream.seek(0)
    valid = (suffix == '.pdf' and signature.startswith(b'%PDF-')) or (suffix == '.doc' and signature == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')
    if suffix == '.docx':
        try:
            with zipfile.ZipFile(stream) as archive:
                valid = {'[Content_Types].xml', 'word/document.xml'}.issubset(archive.namelist())
        except (zipfile.BadZipFile, OSError):
            valid = False
        finally:
            stream.seek(0)
    if not valid:
        raise ValueError("Fayl tarkibi tanlangan formatga mos emas.")
    stored = f'/static/uploads/special_issues/{uuid.uuid4().hex}{suffix}'
    path = document_path(root, stored)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        upload.save(path)
    except Exception:
        if os.path.isfile(path):
            os.remove(path)
        raise
    return {'filepath': stored, 'filename': filename[:200], 'size': size, 'format': suffix[1:].upper()}


def remove_document_file(root, document):
    path = document_path(root, document.get('filepath'))
    if path and os.path.isfile(path):
        os.remove(path)


def localized(value, language):
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ''
    return next((value.get(lang) for lang in (language, 'uz', 'en', 'ru') if isinstance(value.get(lang), str) and value.get(lang)), '')


def public_details(data, language):
    data = decode_details(data)
    result = {field: localized(data.get(field), language) for field in LOCALIZED_FIELDS}
    result['event_date'] = data.get('event_date') or ''
    result['documents'] = documents_from(data)
    return result


UI = {
    'uz': dict(special='Maxsus son', about='Maxsus son haqida', documents='Hujjatlar', articles='Ushbu sondagi maqolalar', letter='Axborot xati', letter_hint="Tadbir yo'nalishlari, muhim sanalar va mualliflar uchun talablar.", download_letter='Axborot xatini yuklab olish', primary='Asosiy hujjat', additional="Qo'shimcha hujjatlar", organizer='Tashkilotchi', venue="O'tkazilish joyi", event_date='Tadbir sanasi', publication_languages='Nashr tillari', read="Maqolalarni o'qish", search="Maqola yoki muallifni qidirish…", empty="Qidiruvga mos maqola topilmadi.", program='Konferensiya dasturi', template='Maqola shabloni', committee="Tashkiliy qo'mita", other='Boshqa hujjat', masters='Magistratura seriyasi', phd='Doktorantura seriyasi', teacher="Professor-o'qituvchilar seriyasi"),
    'ru': dict(special='Специальный выпуск', about='О специальном выпуске', documents='Документы', articles='Статьи выпуска', letter='Информационное письмо', letter_hint='Направления мероприятия, важные даты и требования к авторам.', download_letter='Скачать информационное письмо', primary='Основной документ', additional='Дополнительные документы', organizer='Организатор', venue='Место проведения', event_date='Дата мероприятия', publication_languages='Языки публикации', read='Читать статьи', search='Поиск по статье или автору…', empty='Статьи не найдены.', program='Программа конференции', template='Шаблон статьи', committee='Организационный комитет', other='Другой документ', masters='Серия: Магистратура', phd='Серия: Докторантура', teacher='Серия: Профессорско-преподавательский состав'),
    'en': dict(special='Special issue', about='About this issue', documents='Documents', articles='Articles in this issue', letter='Information letter', letter_hint='Event topics, important dates and requirements for authors.', download_letter='Download information letter', primary='Main document', additional='Additional documents', organizer='Organizer', venue='Location', event_date='Event date', publication_languages='Publication languages', read='Read articles', search='Search articles or authors…', empty='No matching articles found.', program='Conference programme', template='Article template', committee='Organizing committee', other='Other document', masters="Master's series", phd='Doctoral series', teacher='Academic staff series'),
}


def ui_texts(language):
    return UI.get(language, UI['uz'])
