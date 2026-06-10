# Mainweb asosiy kodlari jamlanmasi

Sana: 2026-06-05  
Loyiha qismi: `mainweb`

Ushbu hujjat `mainweb` web-ilovasining hujjat uchun kerakli asosiy kodlari va izohlarini jamlaydi. Loyiha Flask asosida yozilgan, PostgreSQL bilan ishlaydi, foydalanuvchi autentifikatsiyasi, maqola yuborish, maqola/sonlarni ko'rish, to'lov va tarjima funksiyalarini o'z ichiga oladi.

## 1. Mainweb papkasi vazifasi

`mainweb` - saytning ommaviy web qismi va muallif kabineti. Bu qismda quyidagi asosiy modullar bor:

| Fayl | Vazifasi |
| --- | --- |
| `mainweb/run.py` | Flask ilovasini ishga tushiradi |
| `mainweb/app.py` | Flask app yaratadi, route/modul/filterlarni ulaydi |
| `mainweb/settings.py` | `.env` va konfiguratsiyalarni o'qiydi |
| `mainweb/extensions.py` | PostgreSQL connector obyektini yaratadi |
| `mainweb/modules/connector.py` | DB bilan ishlash uchun query builder |
| `mainweb/modules/translate.py` | Ko'p tilli tarjima mexanizmi |
| `mainweb/routes/public.py` | Ommaviy sahifalar: bosh sahifa, maqolalar, sonlar, yangiliklar |
| `mainweb/routes/auth.py` | Login, register, email verification, Google/ORCID auth |
| `mainweb/routes/dashboard.py` | Muallif kabineti, maqola yuborish, profil, xaridlar |
| `mainweb/routes/api.py` | JSON API: maqola saqlash/yuborish, upload, to'lov |
| `mainweb/utils/auth.py` | Login decoratorlari, parol/email tekshirish |
| `mainweb/utils/roles.py` | Rollar va permissionlar |
| `mainweb/utils/uploads.py` | Upload papkalari va ruxsat etilgan fayllar |
| `mainweb/templates/basic.html` | Asosiy HTML layout |
| `mainweb/templates/index.html` | Bosh sahifa shabloni |
| `mainweb/templates/mainweb/article.html` | Maqola sahifasi shabloni |

## 2. Ishga tushirish kodi

Fayl: `mainweb/run.py`

```python
import os

from app import create_app

app = create_app()


def _env_flag(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {'1', 'true', 'yes', 'on'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=_env_flag('FLASK_DEBUG'))
```

Bu kod `create_app()` orqali Flask ilovasini yaratadi va lokal serverda `0.0.0.0:5000` portida ishga tushiradi.

## 3. Flask ilovani yig'ish

Fayl: `mainweb/app.py`

```python
def create_app():
    app = Flask(__name__)
    _configure_logging(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    app.secret_key = settings.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = bool(settings.IS_PRODUCTION)
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400

    @app.get('/healthz')
    def healthz():
        return jsonify({'status': 'ok', 'service': 'mainweb', 'version': settings.APP_VERSION}), 200

    Swagger(app, config=swagger_config, template=swagger_template)

    init_uploads(app)
    register_filters(app)
    hooks.register(app)
    context.register_context_processors(app)
    auth.run_runtime_schema_syncs()
    api.run_runtime_schema_syncs()
    _migrate_legacy_password_hashes()

    auth.register(app)
    public.register(app)
    dashboard.register(app)
    api.register(app)

    return app
```

Asosiy vazifalari:

- Flask app yaratadi.
- Session xavfsizligini sozlaydi.
- `/healthz` endpointini beradi.
- Swagger API hujjatini ulaydi.
- Upload, filter, hook, context processorlarni ro'yxatdan o'tkazadi.
- `auth`, `public`, `dashboard`, `api` route modullarini appga ulaydi.

## 4. Konfiguratsiya

Fayl: `mainweb/settings.py`

```python
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

FLASK_ENV = os.getenv('FLASK_ENV', '').strip().lower()
IS_PRODUCTION = FLASK_ENV == 'production'


def _get_env(name, default=None, production_required=False):
    value = os.getenv(name)
    if value is not None and str(value).strip() != '':
        return value
    if production_required and IS_PRODUCTION:
        raise RuntimeError(f'{name} environment variable must be set in production')
    return default


DB_HOST = _get_env('DB_HOST', '127.0.0.1')
DB_PORT = int(_get_env('DB_PORT', 5432))
DB_USER = _get_env('DB_USER', 'postgres')
DB_PASSWORD = _get_env('DB_PASSWORD', '1', production_required=True)
DB_NAME = _get_env('DB_NAME', 'journal2')
APP_HOST = _get_env('APP_HOST', 'localhost:8080')
SAVE_PATH = _get_env('SAVE_PATH', '/var/www/journal/')
SECRET_KEY = _get_env('SECRET_KEY', 'dev-mainweb-secret-key-change-me', production_required=True)
APP_VERSION = _get_env('APP_VERSION', '0.0.0')
LOG_LEVEL = _get_env('LOG_LEVEL', 'INFO')
```

Bu fayl `.env` ichidagi DB, mail, OAuth, security va app sozlamalarini o'qiydi. Production rejimida kuchsiz default secretlardan foydalanishga ruxsat bermaydi.

## 5. Database connector

Fayl: `mainweb/extensions.py`

```python
from modules.connector import PostgreSQLConnector
try:
    import mainweb.settings as settings
except ImportError:
    import settings

dbc = PostgreSQLConnector(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    database=settings.DB_NAME,
)
```

`dbc` butun `mainweb` bo'ylab ishlatiladigan asosiy database obyektidir. Masalan:

```python
publications = dbc.publications.get().exec()
user = dbc.users.get(email=email).exec()
dbc.submissions.add(**db_payload).exec()
dbc.publications.get(id=article_id).update(stat_views=new_views).exec()
```

## 6. Tarjima mexanizmi

Fayl: `mainweb/modules/translate.py`

```python
def translate(data):
    if not data:
        return data

    current_lang = session.get('language', 'en')
    if current_lang == 'en':
        return _decode_record_strings(data)

    fields = list(data.keys())
    keys_to_delete = []

    for field in fields:
        if field.endswith('_uz') or field.endswith('_ru'):
            keys_to_delete.append(field)
            continue

        if current_lang == 'uz' and f'{field}_uz' in data:
            data[field] = '' if data.get(f'{field}_uz') is None else data.get(f'{field}_uz')
            keys_to_delete.append(f'{field}_uz')
        elif current_lang == 'ru' and f'{field}_ru' in data:
            data[field] = '' if data.get(f'{field}_ru') is None else data.get(f'{field}_ru')
            keys_to_delete.append(f'{field}_ru')

    for key in keys_to_delete:
        if key in data:
            del data[key]

    return _decode_record_strings(data)
```

```python
def t(key):
    current_lang = session.get('language', 'en')
    translations_cache = _load_translations_from_db()

    if current_lang in translations_cache and key in translations_cache[current_lang]:
        translation = translations_cache[current_lang][key]
        if _translation_is_usable(translation, key):
            return _decode_entities(translation)

    static_lang = _static_translations.get(current_lang, {})
    if key in static_lang and _translation_is_usable(static_lang[key], key):
        return _decode_entities(static_lang[key])

    if key in translations_cache['en']:
        translation = translations_cache['en'][key]
        if _translation_is_usable(translation, key):
            return _decode_entities(translation)

    return _humanize_translation_key(key)
```

`translate(data)` obyekt ichidagi `title_uz`, `title_ru` kabi maydonlarni tanlangan tilga qarab asosiy `title` maydoniga joylaydi. `t(key)` esa interfeys matnlari uchun tarjimani DB yoki static lug'atlardan olib beradi.

## 7. Auth va permission helperlar

Fayl: `mainweb/utils/auth.py`

```python
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('app__login'))

        user_id = session.get('user_id')
        user_data = dbc.users.get(id=user_id).exec()
        if not user_data or user_data[0].get('is_blocked') or user_data[0].get('is_hidden'):
            session.pop('user_id', None)
            session.pop('user', None)
            flash('Your account is blocked. Please contact support.', 'error')
            return redirect(url_for('app__login'))

        user_row = hydrate_user_roles(user_data[0])
        session['user'] = _normalize_session_user(user_row)
        return f(*args, **kwargs)
    return decorated_function
```

```python
def author_login_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        user_rows = dbc.users.get(id=user_id).exec()
        user_row = hydrate_user_roles(user_rows[0] if user_rows else session.get('user') or {})

        if user_has_permission(user_row, 'website.dashboard.access') or user_has_permission(user_row, 'fmadmin.access'):
            return f(*args, **kwargs)

        flash("Bu akkaunt uchun maqola yuborish roli yoqilmagan.", 'warning')
        return redirect(url_for('app__index'))

    return decorated_function
```

Fayl: `mainweb/utils/roles.py`

```python
ROLE_PERMISSIONS = {
    'user': {
        'website.dashboard.access',
        'website.submissions.create',
    },
    'editor': {
        'fmadmin.access',
        'fmadmin.dashboard.editor',
        'fmadmin.assignments.view',
        'fmadmin.assignments.review',
        'fmadmin.notifications.view',
    },
    'admin': {
        'fmadmin.access',
        'fmadmin.dashboard.admin',
        'fmadmin.submissions.manage',
        'fmadmin.assignments.manage',
        'fmadmin.notifications.view',
    },
    'superadmin': {
        'fmadmin.access',
        'fmadmin.dashboard.admin',
        'fmadmin.submissions.manage',
        'fmadmin.users.manage',
        'fmadmin.content.manage',
        'fmadmin.finance.manage',
        'fmadmin.system.manage',
    },
}
```

Bu qismda `user`, `editor`, `admin`, `superadmin` rollari va ularning ruxsatlari belgilanadi.

## 8. Public route endpointlari

Fayl: `mainweb/routes/public.py`

```python
def register(app):
    app.add_url_rule('/', view_func=app__index)
    app.add_url_rule('/editorial', view_func=app__editorial)
    app.add_url_rule('/page/<string:alias>', view_func=app__page_alias)
    app.add_url_rule('/payment-guide', view_func=app__payment_guide)
    app.add_url_rule('/contact', view_func=app__contact, methods=['GET', 'POST'])
    app.add_url_rule('/articles', view_func=app__articles)
    app.add_url_rule('/news', view_func=app__news)
    app.add_url_rule('/news/<int:news_id>', view_func=app__news_detail)
    app.add_url_rule('/issues', view_func=app__issues)
    app.add_url_rule('/issue/<int:issue_id>', view_func=app__issue)
    app.add_url_rule('/issue/download/<int:issue_id>', view_func=app__download_issue)
    app.add_url_rule('/article/<int:article_id>', view_func=app__article)
    app.add_url_rule('/article/download/<int:article_id>', view_func=app__download_article)
```

Asosiy sahifalar:

| URL | Funksiya | Vazifa |
| --- | --- | --- |
| `/` | `app__index` | Bosh sahifa |
| `/articles` | `app__articles` | Maqolalar ro'yxati |
| `/article/<id>` | `app__article` | Bitta maqola sahifasi |
| `/article/download/<id>` | `app__download_article` | Maqola faylini yuklab olish |
| `/issues` | `app__issues` | Jurnal sonlari |
| `/issue/<id>` | `app__issue` | Bitta son sahifasi |
| `/news` | `app__news` | Yangiliklar |
| `/contact` | `app__contact` | Aloqa sahifasi |

## 9. Bosh sahifa kodi

Fayl: `mainweb/routes/public.py`

```python
def app__index():
    if 'language' not in session:
        browser_lang = request.accept_languages.best_match(['uz', 'ru', 'en'])
        session['language'] = browser_lang or 'en'
        session.modified = True

    current_lang = _current_lang_code()

    def _home_publications():
        nonlocal _home_publications_cache
        if _home_publications_cache is None:
            _home_publications_cache = dbc.publications.get().exec() or []
        return _home_publications_cache

    def _home_visible_publications():
        nonlocal _home_visible_publications_cache
        if _home_visible_publications_cache is None:
            _home_visible_publications_cache = [
                row for row in _home_publications()
                if not _is_masters_publication(row, issue_cache=issue_cache_for_masters)
            ]
        return _home_visible_publications_cache
```

Bosh sahifa foydalanuvchi tilini aniqlaydi, oxirgi sonlar, mashhur maqolalar, mualliflar, statistikalar va sayt bloklari uchun ma'lumotlarni bazadan yig'adi.

## 10. Maqolalar ro'yxati

Fayl: `mainweb/routes/public.py`

```python
def app__articles():
    current_lang = _current_lang_code()
    page = max(request.args.get('page', 1, type=int) or 1, 1)
    per_page = 20

    search_query = request.args.get('search', '').strip()
    issue_filter = request.args.get('issue', '').strip()
    volume_filter = request.args.get('volume', '')
    year_filter = request.args.get('year', '').strip()
    access_filter = request.args.get('access', '').strip().lower()
    sort_by = request.args.get('sort', 'newest').strip().lower()

    valid_sort_options = {'newest', 'oldest', 'title_az', 'title_za', 'most_viewed', 'most_cited'}
    if sort_by not in valid_sort_options:
        sort_by = 'newest'

    query = dbc.publications.get()
    publications = query.exec()

    for publication in publications:
        translate(publication)
        _apply_localized_content(publication, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)
```

Bu funksiya maqolalarni qidirish, yil/son/jild bo'yicha filterlash, access turi bo'yicha ajratish va sort qilish imkonini beradi.

## 11. Maqola sahifasi

Fayl: `mainweb/routes/public.py`

```python
def app__article(article_id):
    current_lang = _current_lang_code()
    viewer_user_id = session.get('user_id')
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = publication[0]
    publication = translate(publication)
    _apply_localized_content(publication, ('title', 'abstract', 'keywords', 'price'), lang=current_lang)

    if publication.get('doi') and not publication.get('doi_link'):
        publication['doi_link'] = f"https://doi.org/{publication.get('doi')}"

    references_count = len(dbc.publication_refs.get(publication_id=article_id).exec())
    citations_count = len(dbc.publication_citations.get(publication_id=article_id).exec())
    publication['references_count'] = references_count
    publication['citations_count'] = citations_count

    if _should_increment_article_view(article_id, user_id=viewer_user_id):
        new_views = (publication.get('stat_views') or 0) + 1
        dbc.publications.get(id=article_id).update(stat_views=new_views).exec()
        publication['stat_views'] = new_views
```

Bu funksiya bitta maqolani ochadi, tarjima qiladi, DOI linkini tayyorlaydi, references/citations sonini hisoblaydi va ko'rish statistikasini oshiradi.

## 12. Maqola yuklab olish

Fayl: `mainweb/routes/public.py`

```python
def app__download_article(article_id):
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = publication[0]
    requires_access = bool(publication.get('is_paid') or publication.get('subscription_enable'))
    access_context = {'has_access': True, 'access_via': 'open', 'tariff': None}

    if requires_access:
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to download this article', 'error')
            return redirect(url_for('app__login'))

        access_context = _resolve_article_access_context(publication, user_id)
        if not access_context.get('has_access'):
            flash('Access denied. Please purchase or subscribe.', 'error')
            return redirect(url_for('app__article', article_id=article_id))
```

Pullik yoki subscription talab qiladigan maqolalarda foydalanuvchi login bo'lganini va ruxsati borligini tekshiradi.

## 13. Auth route endpointlari

Fayl: `mainweb/routes/auth.py`

```python
def register(app):
    app.add_url_rule('/login', view_func=not_auth_only(app__login), methods=['GET', 'POST'])
    app.add_url_rule('/register', view_func=not_auth_only(app__register), methods=['GET', 'POST'])
    app.add_url_rule('/register/verify', view_func=not_auth_only(app__register_verify), methods=['GET', 'POST'])
    app.add_url_rule('/forgot-password', view_func=not_auth_only(app__forgot_password), methods=['GET', 'POST'])
    app.add_url_rule('/forgot-password/verify', view_func=not_auth_only(app__forgot_password_verify), methods=['GET', 'POST'])
    app.add_url_rule('/auth/google', view_func=not_auth_only(app__google_auth_start), methods=['GET'])
    app.add_url_rule('/auth/orcid', view_func=not_auth_only(app__orcid_auth_start), methods=['GET'])
    app.add_url_rule('/logout', view_func=app__logout, methods=['POST'])
```

## 14. Login kodi

Fayl: `mainweb/routes/auth.py`

```python
def app__login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('app__login'))

        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('app__login'))

        _user = dbc.users.get(email=email).exec()
        if _user:
            user = _normalize_user_for_session(_user[0])
            stored_pw = user.get('password', '')

            if stored_pw and stored_pw.startswith(('pbkdf2:', 'scrypt:')):
                password_valid = check_password_hash(stored_pw, password)
            elif stored_pw:
                password_valid = (stored_pw == password)
                if password_valid:
                    hashed = generate_password_hash(password)
                    dbc.users.get(id=user['id']).update(password=hashed).exec()

            if password_valid:
                _set_user_session(user)
                return _post_auth_redirect(user)

        flash('Invalid login or password. Try again.', 'error')
        return redirect(url_for('app__login'))

    return render_template('auth/login.html')
```

Login jarayonida email formati, parol, bloklangan foydalanuvchi holati va eski plaintext parollarni hashga o'tkazish tekshiriladi.

## 15. Register kodi

Fayl: `mainweb/routes/auth.py`

```python
def app__register():
    if request.method == 'POST':
        first_name = sanitize_input(request.form.get('first_name', '').strip())
        last_name = sanitize_input(request.form.get('last_name', '').strip())
        father_name = sanitize_input(request.form.get('father_name', '').strip())
        country = request.form.get('country', '').strip()
        email = request.form.get('email', '').strip().lower()
        email_confirm = request.form.get('email_confirm', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if not all([first_name, last_name, email, email_confirm, password, password_confirm, country]):
            flash('All fields are required', 'error')
            return redirect(url_for('app__register'))

        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('app__register'))

        if email != email_confirm:
            flash('Emails do not match', 'error')
            return redirect(url_for('app__register'))

        if password != password_confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('app__register'))

        valid_password, message = is_strong_password(password)
        if not valid_password:
            flash(message, 'error')
            return redirect(url_for('app__register'))
```

Ro'yxatdan o'tishda kerakli maydonlar, email, parol mosligi va parol kuchliligi tekshiriladi.

## 16. Dashboard endpointlari

Fayl: `mainweb/routes/dashboard.py`

```python
def register(app):
    app.add_url_rule('/dashboard', view_func=author_login_required(app__dashboard))
    app.add_url_rule('/dashboard/articles', view_func=author_login_required(app__dashboard_articles))
    app.add_url_rule('/dashboard/articles/delete/<int:submission_id>', view_func=author_login_required(app__dashboard_articles_delete), methods=['POST'])
    app.add_url_rule('/dashboard/purchases', view_func=author_login_required(app__dashboard_purchases))
    app.add_url_rule('/dashboard/new_article', view_func=author_login_required(app__dashboard_new_article))
    app.add_url_rule('/dashboard/new_article/<track>', view_func=author_login_required(app__dashboard_new_article_track))
    app.add_url_rule('/dashboard/payments', view_func=author_login_required(app__dashboard_payments))
    app.add_url_rule('/dashboard/guides', view_func=author_login_required(app__dashboard_guides))
    app.add_url_rule('/dashboard/notifications', view_func=author_login_required(app__dashboard_notifications))
    app.add_url_rule('/dashboard/profile', view_func=author_login_required(app__dashboard_profile), methods=['GET', 'POST'])
```

## 17. Dashboard bosh sahifa

Fayl: `mainweb/routes/dashboard.py`

```python
def app__dashboard():
    user_id = session['user_id']
    all_submissions = dbc.submissions.get().equal(user_id=user_id).order_by('id').exec()

    drafts_count = 0
    visible_submissions = []
    for submission in all_submissions:
        translate(submission)
        status = (submission.get('status') or '').strip().lower()
        if status == 'draft':
            drafts_count += 1
            continue
        _decorate_submission_with_workflow(submission)
        visible_submissions.append(submission)

    dashboard_stats = {
        'total': len(visible_submissions),
        'drafts': drafts_count,
        'unread_notifications': _count_dashboard_unread_notifications(user_id)
    }

    return render_template(
        'dashboard/index.html',
        submissions=visible_submissions[:4],
        dashboard_stats=dashboard_stats
    )
```

Muallif kabinetida foydalanuvchining yuborgan maqolalari, draftlari, statuslari va notification statistikasi ko'rsatiladi.

## 18. Maqola yuborish sahifasi

Fayl: `mainweb/routes/dashboard.py`

```python
def app__dashboard_new_article():
    submission_id = request.args.get('id', type=int)
    track = _resolve_submission_track(request.args.get('track'))

    if not submission_id and not track:
        return render_template('dashboard/new_article_type.html', submission_tracks=_submission_track_list())

    translations = dbc.translations.get().exec()
    authors = dbc.author_profile.get().exec()
    classifications = dbc.fix_classifications.get().exec()
    countries = dbc.fix_country.get().exec()

    for author in authors:
        author = translate(author)
    for classification in classifications:
        classification = translate(classification)
    for country in countries:
        country = translate(country)

    return render_template(
        'dashboard/new_article.html',
        translations=translations,
        authors=authors,
        classifications=classifications,
        countries=countries,
        selected_track=track,
        selected_track_info=SUBMISSION_TRACKS.get(track)
    )
```

Bu qism maqola yuborish formasiga kerakli tarjimalar, mualliflar, klassifikatsiyalar va davlatlar ro'yxatini beradi.

## 19. API endpointlari

Fayl: `mainweb/routes/api.py`

```python
def register(app):
    app.add_url_rule('/api/getauthor', view_func=author_login_required(app__api_getauthor), methods=['POST'])
    app.add_url_rule('/api/getcurrentauthor', view_func=author_login_required(app__api_getcurrentauthor), methods=['GET'])
    app.add_url_rule('/api/getclassifications', view_func=author_login_required(app__api_getclassifications), methods=['GET'])
    app.add_url_rule('/api/article/save', view_func=author_login_required(app__api_article_save), methods=['POST'])
    app.add_url_rule('/api/article/submit', view_func=author_login_required(app__api_article_submit), methods=['POST'])
    app.add_url_rule('/api/article/upload', view_func=author_login_required(app__api_article_upload), methods=['POST'])
    app.add_url_rule('/api/article/load/<int:submission_id>', view_func=author_login_required(app__api_article_load))
    app.add_url_rule('/api/payment/submit_proof', view_func=login_required(app__api_payment_submit_proof), methods=['POST'])
    app.add_url_rule('/api/payment/create_subscription', view_func=login_required(app__api_payment_create_subscription), methods=['POST'])
    app.add_url_rule('/api/issue/purchase', view_func=login_required(app__api_issue_purchase), methods=['POST'])
    app.add_url_rule('/api/article/purchase', view_func=login_required(app__api_article_purchase), methods=['POST'])
```

## 20. Draft saqlash API

Fayl: `mainweb/routes/api.py`

```python
def app__api_article_save():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json() or {}
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission_id = _parse_int(data.get('submission_id'))

    existing = {}
    if submission_id:
        existing_rows = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
        if not existing_rows:
            return jsonify({'success': False, 'message': 'Submission not found'})
        existing = existing_rows[0]

    submission_payload = _prepare_submission_payload(
        data=data,
        user_id=user_id,
        status='draft',
        existing=existing,
        is_new=not bool(existing)
    )
    draft_errors = _validate_submission_for_draft(submission_payload)
```

Bu endpoint maqolani draft sifatida saqlaydi. Agar oldin yaratilgan `submission_id` bo'lsa, mavjud draftni yangilaydi.

## 21. Maqolani yuborish API

Fayl: `mainweb/routes/api.py`

```python
def app__api_article_submit():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json() or {}
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission_id = _parse_int(data.get('submission_id'))

    submission_payload = _prepare_submission_payload(
        data=data,
        user_id=user_id,
        status='submitted',
        existing=existing,
        is_new=not bool(existing)
    )
    submit_errors = _validate_submission_for_submit(submission_payload)
    if submit_errors:
        return jsonify({
            'success': False,
            'errors': submit_errors,
            'message': 'Validation failed',
            'is_ready_submit': False
        })
```

Bu endpoint draftdan farqli ravishda maqolani tekshiradi va `submitted` statusida tizimga yuboradi. Keyin admin/editor tarafga notification yuboriladi.

## 22. Fayl upload API

Fayl: `mainweb/routes/api.py`

```python
def app__api_article_upload():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['file']
    file_type = (request.form.get('file_type') or request.form.get('type') or 'authors').strip().lower()

    if file and allowed_file(file.filename, {'pdf', 'doc', 'docx'}):
        filename = secure_filename(file.filename)
        filename = f"{file_type}_{user_id}_{int(time.time())}_{filename}"
        filepath = os.path.join(settings.SAVE_PATH, 'private_uploads', 'articles', filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)

        file_ref = build_private_upload_ref('articles', filename)
        download_url = upload_access_url(file_ref)

        return jsonify({
            'success': True,
            'file_ref': file_ref,
            'download': download_url,
            'file_type': file_type
        })
```

Maqola fayllari `pdf`, `doc`, `docx` formatlarida qabul qilinadi va private upload papkasiga saqlanadi.

## 23. Asosiy HTML layout

Fayl: `mainweb/templates/basic.html`

```html
<!doctype html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token }}">
    <title>{% block title %}Philology Matters{% endblock %}</title>
    <link rel="icon" href="/static/favicon.ico">
    <link href="{{ asset_url('styles.css') }}" rel="stylesheet">
</head>

<body class="min-h-screen flex flex-col bg-[#FAFBFC]">
    <main class="site-main flex-1">
        {% block content %}
        You cannot run directly basic.html
        {% endblock %}
    </main>

    {% block footer %}
    {% include 'components/footer/main.html' %}
    {% endblock %}

    {% block scripts %}{% endblock %}
</body>
</html>
```

Bu shablon barcha sahifalar uchun umumiy layout hisoblanadi. Boshqa HTML fayllar `{% extends 'basic.html' %}` orqali undan foydalanadi.

## 24. Bosh sahifa shabloni

Fayl: `mainweb/templates/index.html`

```html
{% extends 'basic.html' %}
{% from 'components/author_tooltip_macros.html' import render_author_list %}

{% block title %}{{ t('website_title') }}{% endblock %}

{% block content %}
{% include 'components/headers/main_header.html' %}
{% include 'components/hero/main_hero.html' %}
{% include 'components/stats_bar.html' %}
{% include 'components/indexing_platforms.html' %}

<div class="container mx-auto px-4 py-10">
    <div class="flex flex-col xl:flex-row gap-6 xl:gap-8">
        <aside class="xl:w-56 shrink-0 order-2 xl:order-1">
            ...
        </aside>

        <div class="flex-1 min-w-0 space-y-8 order-1 xl:order-2">
            ...
        </div>
    </div>
</div>
{% endblock %}
```

Bosh sahifa header, hero, statistika, indexing platformalar, chap sidebar, asosiy kontent va qo'shimcha bloklardan iborat.

## 25. Maqola sahifasi shabloni

Fayl: `mainweb/templates/mainweb/article.html`

```html
{% extends 'basic.html' %}
{% from 'components/author_tooltip_macros.html' import render_author, render_author_list %}

{% block title %}{{ publication.title }} - {{ t('website_title') }}{% endblock %}

{% block head_meta %}
<link rel="canonical" href="{{ request.base_url }}">
<meta property="og:type" content="article">
<meta property="og:title" content="{{ publication.title|striptags }}">
<meta property="og:description" content="{{ (publication.abstract or publication.title or '')|striptags|trim|truncate(220, True, '') }}">
{% if scholar_meta %}
    {% if scholar_meta.title %}<meta name="citation_title" content="{{ scholar_meta.title }}">{% endif %}
    {% for author_name in scholar_meta.authors %}
        <meta name="citation_author" content="{{ author_name }}">
    {% endfor %}
    {% if scholar_meta.doi %}<meta name="citation_doi" content="{{ scholar_meta.doi }}">{% endif %}
    {% if scholar_meta.pdf_url %}<meta name="citation_pdf_url" content="{{ scholar_meta.pdf_url }}">{% endif %}
{% endif %}
{% endblock %}
```

Maqola sahifasida SEO, OpenGraph va Google Scholar uchun `citation_*` meta teglari mavjud.

## 26. Context processorlar

Fayl: `mainweb/routes/context.py`

```python
def register_context_processors(app):
    @app.context_processor
    def inject_latest_issue():
        issues = [
            issue for issue in (dbc.issues.get().exec() or [])
            if not _is_masters_issue_alias(issue.get('category'))
        ]
        if not issues:
            return {'latest_issue': None}

        latest_issue_item = max(issues, key=_latest_issue_sort_key)
        latest_issue_item = dict(latest_issue_item)
        latest_issue_item['title'] = _localized_field(latest_issue_item, 'title')
        latest_issue_item['shortinfo'] = _localized_field(latest_issue_item, 'shortinfo')
        return {'latest_issue': latest_issue_item}

    @app.context_processor
    def inject_translations():
        return dict(t=t)

    @app.context_processor
    def inject_version():
        return {'app_version': settings.APP_VERSION}
```

Context processorlar template ichida global ishlatiladigan `latest_issue`, `t`, `app_version`, formatters va notification ma'lumotlarini beradi.

## 27. Umumiy ishlash oqimi

1. `mainweb/run.py` ishga tushadi.
2. `mainweb/app.py` ichidagi `create_app()` Flask ilovasini yaratadi.
3. `settings.py` `.env` konfiguratsiyalarni yuklaydi.
4. `extensions.py` `dbc` database connectorni yaratadi.
5. `auth`, `public`, `dashboard`, `api` route fayllari appga ulanadi.
6. Foydalanuvchi sahifa ochsa, route DBdan ma'lumot oladi.
7. `translate()` tanlangan tilga qarab maydonlarni moslaydi.
8. Route `render_template()` orqali HTML templatega data yuboradi.
9. Dashboard va API endpointlar login/permission decoratorlari bilan himoyalangan.

## 28. Hujjat uchun qisqa xulosa

`mainweb` qismi jurnal web-saytining foydalanuvchi ko'radigan asosiy qismidir. U bosh sahifa, maqolalar, jurnal sonlari, yangiliklar, muallif kabineti, ro'yxatdan o'tish, login, maqola yuborish, fayl upload qilish, to'lov va tarjima funksiyalarini bajaradi. Arxitektura Flask route modullari asosida tuzilgan: `public.py` ommaviy sahifalarni, `auth.py` autentifikatsiyani, `dashboard.py` muallif kabinetini, `api.py` esa AJAX/JSON so'rovlarni boshqaradi. Ma'lumotlar PostgreSQL bazasidan `dbc` connector orqali olinadi va `Jinja2` template orqali frontendga chiqariladi.
