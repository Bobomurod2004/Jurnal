import os
# flake8: noqa
import uuid
import datetime
import secrets
import re
from urllib.parse import urlencode
from flask import Blueprint, send_from_directory, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from modules.translate import t, translate
from extensions import db
import settings
from utils.auth import is_allowed, is_editor_allowed, is_admin_or_editor
from services.stats import (
    calculate_dashboard_stats,
    get_submissions_stats,
    get_monthly_articles_stats,
    get_recent_submissions,
    get_top_articles,
)

bp = Blueprint('fmadmin_web', __name__)

def new_alert(message, category='info'):
    flash(message, category)

@bp.route('/fmadmin/lang/<lang_code>')
def set_language(lang_code):
    if lang_code in ['en', 'ru', 'uz']:
        session['language'] = lang_code
    return redirect(request.referrer or url_for('index'))

@bp.route('/fmadmin/')
@is_allowed
def index():
    # Calculate dashboard statistics
    stats = calculate_dashboard_stats()
    
    # Get submissions statistics for chart
    submissions_stats = get_submissions_stats()
    
    # Get monthly articles statistics for chart
    monthly_stats = get_monthly_articles_stats()
    
    # Get recent submissions
    recent_submissions = get_recent_submissions()
    
    # Get top articles by views
    top_articles = get_top_articles()
    
    return render_template('index.html', 
                         stats=stats,
                         submissions_stats=submissions_stats,
                         monthly_stats=monthly_stats,
                         recent_submissions=recent_submissions,
                         top_articles=top_articles)

@bp.route('/fmadmin/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже авторизован, перенаправляем на главную
    if 'fmadmin_user' in session and session['fmadmin_user'].get('rolename') in ['admin', 'editor']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash(t('admin_error_fill_all_fields'), 'danger')
            return render_template('auth/login.html')

        user = db.users.all().equal(email=email).exec()
        if not user:
            flash(t('admin_error_invalid_credentials'), 'danger')
            return render_template('auth/login.html')

        from werkzeug.security import check_password_hash, generate_password_hash
        user = user[0]

        # Проверяем пароль
        password_valid = False
        stored_password = user.get('password')
        
        if stored_password and (stored_password.startswith('pbkdf2:sha256:') or stored_password.startswith('scrypt:')):
            password_valid = check_password_hash(stored_password, password)
        else:
            # Plain text comparison
            password_valid = (stored_password == password)
            if password_valid:
                # Auto-migrate to hash
                hashed = generate_password_hash(password)
                db.users.all().equal(id=user['id']).update(password=hashed).exec()

        if not password_valid:
            flash(t('admin_error_invalid_credentials'), 'danger')
            return render_template('auth/login.html')

        # Проверяем роль (только админы и редакторы)
        if user.get('rolename') not in ['admin', 'editor']:
            flash(t('admin_error_no_access'), 'danger')
            return render_template('auth/login.html')

        # Сохраняем пользователя в сессии
        session['fmadmin_user'] = {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'rolename': user['rolename'],
            'editor_specialization': user.get('editor_specialization')
        }

        flash(f"{t('admin_welcome_body')}, {user['name']}!", 'success')
        return redirect(url_for('index'))

    return render_template('auth/login.html')

@bp.route('/fmadmin/logout')
def logout():
    session.pop('fmadmin_user', None)
    flash(t('admin_success_logout'), 'info')
    return redirect(url_for('login'))

@bp.route('/fmadmin/users/users')
@is_allowed
def users():
    # Получаем номер страницы из параметра запроса
    page = request.args.get('page', 1, type=int)
    per_page = 20
    # Получаем значения фильтров
    search_name = request.args.get('name', '').strip()
    search_email = request.args.get('email', '').strip()
    search_orcid = request.args.get('orcid', '').strip()

    # Формируем запрос к БД с учётом фильтров
    query = db.users.all()
    if search_name:
        query = query.like(name=search_name)
    if search_email:
        query = query.like(email=search_email)
    # ORCID может быть в author_profile, но если его нет в users, пропускаем фильтр
    # query = query.like(orcid=search_orcid) # если поле есть

    total_users = query.copy().count().exec()
    users = query.per_page(per_page).page(page).exec()
    total_pages = (total_users + per_page - 1) // per_page

    # Получаем связанные профили авторов для отображения в колонке "Автор"
    author_profiles = db.author_profile.all().exec()
    author_map = {a['user_id']: a for a in author_profiles if a['user_id'] is not None}
    # Получаем тарифы
    tariffs = db.tariffs.all().exec()
    tariffs_map = {t['id']: t for t in tariffs}

    return render_template('users/users/users.html', users=users, page=page, total_users=total_users, total_pages=total_pages,
                           search_name=search_name, search_email=search_email, search_orcid=search_orcid,
                           author_map=author_map, tariffs_map=tariffs_map)

@bp.route('/fmadmin/users/users/<int:user_id>', methods=['GET', 'POST'])
@is_allowed
def user_edit(user_id):
    if request.method == 'POST':
        
        if user_id == 0:
            # Создание нового пользователя
            name = request.form.get('name')
            second_name = request.form.get('second_name')
            father_name = request.form.get('father_name')
            email = request.form.get('email')
            country_id = request.form.get('country_id')
            region = request.form.get('region')
            rolename = request.form.get('rolename')
            is_blocked = bool(request.form.get('is_blocked'))
            is_notify = bool(request.form.get('is_notify'))
            tariff_id = request.form.get('tariff_id')
            subscription_end_date = parse_date(request.form.get('subscription_end_date'))
            from werkzeug.security import generate_password_hash
            password = request.form.get('password')
            hashed_password = generate_password_hash(password) if password else None
            user_id_new = db.users.add(
                name=name,
                second_name=second_name,
                father_name=father_name,
                email=email,
                country_id=country_id or None,
                region=region,
                rolename=rolename,
                is_blocked=is_blocked,
                is_notify=is_notify,
                password=hashed_password,
                tariff_id=tariff_id or None,
                subscription_end_date=subscription_end_date,
                created_at=int(datetime.datetime.now().timestamp()),
                register_time=int(datetime.datetime.now().timestamp())
            ).exec()
            new_alert('Пользователь успешно сохранён', 'success')
            return redirect(url_for('user_edit', user_id=user_id_new))
        else:
            data = request.json if request.is_json else request.form
            subscription_end_date = parse_date(data.get('subscription_end_date'))
        db.users.all().equal(id=user_id).update(
            name=data.get('name'),
            second_name=data.get('second_name'),
            father_name=data.get('father_name'),
            email=data.get('email'),
            country_id=data.get('country_id') or None,
            region=data.get('region'),
            rolename=data.get('rolename'),
            is_blocked=bool(data.get('is_blocked')),
            is_notify=bool(data.get('is_notify')),
            tariff_id=data.get('tariff_id') or None,
            subscription_end_date=subscription_end_date
        ).exec()
        new_alert('Пользователь успешно сохранён', 'success')
        return redirect(url_for('user_edit', user_id=user_id))

    if user_id == 0:
        # Новый пользователь
        user = {
            'id': 0,
            'name': '',
            'second_name': '',
            'father_name': '',
            'email': '',
            'country_id': None,
            'region': '',
            'rolename': 'user',
            'is_blocked': False,
            'is_notify': False,
            'accept_rules_time': None,
            'last_online': None,
            'created_at': None,
            'register_time': None,
            'tariff_id': None,
            'subscription_end_date': None
        }
        password = uuid.uuid4().hex
    else:
        user = db.users.all().equal(id=user_id).exec()
        if not user:
            return 'Пользователь не найден', 404
        user = user[0]
        password = None
    countries = db.fix_country.all().exec()
    tariffs = db.tariffs.all().exec()
    
    # Проверяем, есть ли у пользователя загруженные документы (для фильтрации тарифов)
    user_has_documents = False
    if user_id > 0:
        user_docs = db.user_doc_uploads.all().equal(user_id=user_id).exec()
        user_has_documents = len(user_docs) > 0
    
    # Фильтруем тарифы: если у пользователя нет документов, скрываем тарифы "для верифицированных"
    filtered_tariffs = []
    for tariff in tariffs:
        if tariff.get('is_verified', False) and not user_has_documents:
            continue  # Пропускаем тарифы для верифицированных, если у пользователя нет документов
        filtered_tariffs.append(tariff)
    
    return render_template('users/users/edit.html', user=user, countries=countries, tariffs=filtered_tariffs, password=password)


@bp.route('/fmadmin/users/authors')
@is_allowed
def authors():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_name = request.args.get('name', '').strip()
    search_orcid = request.args.get('orcid', '').strip()
    search_by_name = request.args.get('search_by_name', '')
    has_articles = request.args.get('has_articles', '')

    query = db.author_profile.all()
    if search_name:
        query = query.like(name=search_name)
    if search_orcid:
        if search_by_name:
            # Поиск по полному имени в поле ORCID
            query = query.like(name=search_orcid)
        else:
            # Обычный поиск по ORCID
            query = query.like(orcid=search_orcid)

    # Получаем id авторов для фильтрации по наличию статей
    if has_articles == 'true':
        # Только авторы, у которых есть публикации как main_author
        author_ids_with_articles = [p['main_author_id'] for p in db.publications.all().exec() if p['main_author_id'] is not None]
        if author_ids_with_articles:
            query = query.any(id=author_ids_with_articles)
        else:
            query = query.any(id=[-1])  # Не будет найдено
    elif has_articles == 'false':
        # Только авторы, у которых нет публикаций как main_author
        author_ids_with_articles = [p['main_author_id'] for p in db.publications.all().exec() if p['main_author_id'] is not None]
        all_author_ids = [a['id'] for a in db.author_profile.all().exec()]
        author_ids_without_articles = list(set(all_author_ids) - set(author_ids_with_articles))
        if author_ids_without_articles:
            query = query.any(id=author_ids_without_articles)
        else:
            query = query.any(id=[-1])

    total_authors = query.copy().count().exec()
    authors = query.per_page(per_page).page(page).exec()
    total_pages = (total_authors + per_page - 1) // per_page

    # Для отображения количества статей как автор/соавтор
    publications = db.publications.all().exec()
    author_stats = {}
    for a in authors:
        as_main = sum(1 for p in publications if p['main_author_id'] == a['id'])
        as_co = sum(1 for p in publications if a['id'] in (p['subauthor_ids'] or []))
        author_stats[a['id']] = {'as_main': as_main, 'as_co': as_co}

    # Для отображения связанного пользователя
    users_map = {u['id']: u for u in db.users.all().exec()}

    return render_template('users/authors/authors.html', authors=authors, page=page, total_authors=total_authors, total_pages=total_pages,
                           search_name=search_name, search_orcid=search_orcid, search_by_name=search_by_name, has_articles=has_articles,
                           author_stats=author_stats, users_map=users_map)

@bp.route('/fmadmin/users/authors/<int:author_id>', methods=['GET', 'POST'])
@is_allowed
def author_edit(author_id):
    if request.method == 'POST':
        if author_id == 0:
            name = request.form.get('name')
            user_id = request.form.get('user_id') or None
            organization = request.form.get('organization')
            email = request.form.get('email')
            position = request.form.get('position')
            address_street = request.form.get('address_street')
            address_country = request.form.get('address_country')
            address_city = request.form.get('address_city')
            address_zip = request.form.get('address_zip')
            phone = request.form.get('phone')
            orcid = request.form.get('orcid')
            department = request.form.get('department')
            created_at = parse_date(request.form.get('created_at'), with_time=True)
            updated_at = parse_date(request.form.get('updated_at'), with_time=True)
            author_id_new = db.author_profile.add(
                user_id=user_id,
                name=name,
                organization=organization,
                email=email,
                position=position,
                address_street=address_street,
                address_country=address_country,
                address_city=address_city,
                address_zip=address_zip,
                phone=phone,
                orcid=orcid,
                department=department,
                created_at=created_at or int(datetime.datetime.now().timestamp()),
                updated_at=updated_at or int(datetime.datetime.now().timestamp())
            ).exec()
            new_alert('Автор успешно создан', 'success')
            return redirect(url_for('author_edit', author_id=author_id_new))
        else:
            data = request.json if request.is_json else request.form
            created_at = parse_date(data.get('created_at'), with_time=True)
            updated_at = parse_date(data.get('updated_at'), with_time=True)
            db.author_profile.all().equal(id=author_id).update(
                user_id=data.get('user_id') or None,
                name=data.get('name'),
                organization=data.get('organization'),
                email=data.get('email'),
                position=data.get('position'),
                address_street=data.get('address_street'),
                address_country=data.get('address_country'),
                address_city=data.get('address_city'),
                address_zip=data.get('address_zip'),
                phone=data.get('phone'),
                orcid=data.get('orcid'),
                department=data.get('department'),
                created_at=created_at,
                updated_at=updated_at or int(datetime.datetime.now().timestamp())
            ).exec()
            new_alert('Автор успешно сохранён', 'success')
            return redirect(url_for('author_edit', author_id=author_id))

    if author_id == 0:
        author = {
            'id': 0,
            'user_id': None,
            'name': '',
            'organization': '',
            'email': '',
            'position': '',
            'address_street': '',
            'address_country': '',
            'address_city': '',
            'address_zip': '',
            'phone': '',
            'orcid': '',
            'department': '',
            'created_at': None,
            'updated_at': None
        }
    else:
        author = db.author_profile.all().equal(id=author_id).exec()
        if not author:
            return 'Автор не найден', 404
        author = author[0]
    # Получить id всех user_id, которые уже привязаны к author_profile
    all_authors = db.author_profile.all().exec()
    used_user_ids = set(a['user_id'] for a in all_authors if a['user_id'])
    # Добавить текущего пользователя, если он есть
    if author.get('user_id'):
        used_user_ids.discard(author['user_id'])
    users = [u for u in db.users.all().exec() if u['id'] not in used_user_ids or u['id'] == author.get('user_id')]
    return render_template('users/authors/edit.html', author=author, users=users)


@bp.route('/fmadmin/website/issues')
@is_allowed
def issues():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    # Получаем значения фильтров
    search_title = request.args.get('title', '').strip()
    search_vol_no = request.args.get('vol_no', '').strip()
    search_issue_no = request.args.get('issue_no', '').strip()
    search_status = request.args.get('status', '').strip()
    # Получаем все выпуски с учётом фильтров
    query = db.issues.all()
    if search_title:
        query = query.like(title=search_title)
    if search_vol_no:
        query = query.like(vol_no=search_vol_no)
    if search_issue_no:
        query = query.like(issue_no=search_issue_no)
    if search_status:
        if search_status == 'published':
            query = query.equal(subscription_enable=True)
        elif search_status == 'draft':
            query = query.equal(subscription_enable=False)
    total_issues = query.copy().count().exec()
    issues = query.per_page(per_page).page(page).exec()
    total_pages = (total_issues + per_page - 1) // per_page
    # Получаем все публикации для подсчёта статей по выпускам
    publications = db.publications.all().exec()
    issue_article_count = {}
    for issue in issues:
        issue_article_count[issue['id']] = sum(1 for p in publications if p['issue_id'] == issue['id'])
    # Формируем query_string для пагинации (без page)
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    return render_template('website/issues/issues.html', issues=issues, page=page, total_issues=total_issues, total_pages=total_pages,
                           issue_article_count=issue_article_count,
                           search_title=search_title, search_vol_no=search_vol_no, search_issue_no=search_issue_no, search_status=search_status,
                           pagination_query_string=pagination_query_string)

def save_file(category, file, allow_exts):
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in allow_exts:
        raise ValueError('Недопустимое расширение файла')
    now = datetime.datetime.now()
    rel_dir = f'static/uploads/{category}/{now.year}/{now.month:02d}'
    abs_dir = os.path.join(settings.SAVE_PATH, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    filename = f'{uuid.uuid4().hex}.{ext}'
    file_path = os.path.join(abs_dir, filename)
    file.save(file_path)
    return f'/{rel_dir}/{filename}'

def save_file_to_db(file, category='articles', comment=''):
    """Сохраняет файл и записывает его в таблицу files, возвращает ID файла"""
    ext = file.filename.rsplit('.', 1)[-1].lower()
    now = datetime.datetime.now()
    rel_dir = f'static/uploads/{category}/{now.year}/{now.month:02d}'
    abs_dir = os.path.join(settings.SAVE_PATH, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    filename = f'{uuid.uuid4().hex}.{ext}'
    file_path = os.path.join(abs_dir, filename)
    file.save(file_path)
    filepath = f'/{rel_dir}/{filename}'

    # Сохраняем в таблицу files
    file_id = db.files.add(
        name=file.filename,
        filepath=filepath,
        upload_time=int(now.timestamp()),
        comment=comment,
        filesize=os.path.getsize(file_path),
        created_at=int(now.timestamp())
    ).exec()

    if isinstance(file_id, list) and file_id:
        file_id = file_id[0]['id']
    elif isinstance(file_id, dict):
        file_id = file_id.get('id')

    return file_id

# Вспомогательные функции для работы с редакторами
def get_current_user():
    """Получить текущего пользователя из сессии"""
    return session.get('fmadmin_user')

def create_editor_notification(editor_id, assignment_id, message):
    """Создать уведомление для редактора"""
    db.editor_notifications.add(
        editor_id=editor_id,
        assignment_id=assignment_id,
        message=message,
        is_read=False,
        created_at=int(datetime.datetime.now().timestamp())
    ).exec()

def get_editors():
    """Получить список всех редакторов"""
    return db.users.all().equal(rolename='editor').exec()

def parse_date(date_str, with_time=False):
    """Парсинг даты из строки"""
    if not date_str:
        return None
    try:
        if with_time:
            return int(datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M').timestamp())
        else:
            return int(datetime.datetime.strptime(date_str, '%Y-%m-%d').timestamp())
    except Exception:
        return None

@bp.route('/fmadmin/website/issues/<int:issue_id>', methods=['GET', 'POST'])
@is_allowed
def issue_edit(issue_id):
    if request.method == 'POST':
        cover_image = None
        if 'cover_image' in request.files and request.files['cover_image'].filename:
            cover_image = save_file('issues', request.files['cover_image'], ['jpg', 'jpeg', 'png', 'gif', 'webp'])
        if issue_id == 0:
            title = request.form.get('title')
            title_uz = request.form.get('title_uz')
            title_ru = request.form.get('title_ru')
            vol_no = request.form.get('vol_no')
            issue_no = request.form.get('issue_no')
            year = request.form.get('year')
            category = request.form.get('category')
            shortinfo = request.form.get('shortinfo')
            shortinfo_uz = request.form.get('shortinfo_uz')
            shortinfo_ru = request.form.get('shortinfo_ru')
            price = request.form.get('price')
            price_uz = request.form.get('price_uz')
            price_ru = request.form.get('price_ru')
            subscription_enable = bool(request.form.get('subscription_enable'))
            is_paid = bool(request.form.get('is_paid'))
            created_at = parse_date(request.form.get('created_at'), with_time=False)
            issue_id_new = db.issues.add(
                title=title,
                title_uz=title_uz,
                title_ru=title_ru,
                vol_no=vol_no,
                issue_no=issue_no,
                year=year,
                category=category,
                shortinfo=shortinfo,
                shortinfo_uz=shortinfo_uz,
                shortinfo_ru=shortinfo_ru,
                price=price,
                price_uz=price_uz,
                price_ru=price_ru,
                subscription_enable=subscription_enable,
                is_paid=is_paid,
                cover_image=cover_image,
                created_at=created_at or int(datetime.datetime.now().timestamp())
            ).exec()
            if issue_id_new:
                issue_id_new = issue_id_new[0]['id']
                new_alert('Выпуск успешно создан', 'success')
            else:
                issue_id_new = 0
                new_alert('Ошибка', 'danger')
            return redirect(url_for('issue_edit', issue_id=issue_id_new))
        else:
            data = request.json if request.is_json else request.form
            created_at = parse_date(data.get('created_at'), with_time=True)
            update_data = dict(
                title=data.get('title'),
                title_uz=data.get('title_uz'),
                title_ru=data.get('title_ru'),
                vol_no=data.get('vol_no'),
                issue_no=data.get('issue_no'),
                year=data.get('year'),
                category=data.get('category'),
                shortinfo=data.get('shortinfo'),
                shortinfo_uz=data.get('shortinfo_uz'),
                shortinfo_ru=data.get('shortinfo_ru'),
                price=data.get('price'),
                price_uz=data.get('price_uz'),
                price_ru=data.get('price_ru'),
                subscription_enable=bool(data.get('subscription_enable')),
                is_paid=bool(data.get('is_paid')),
                created_at=created_at
            )
            if cover_image:
                update_data['cover_image'] = cover_image
            else:
                update_data['cover_image'] = data.get('cover_image')
            db.issues.all().equal(id=issue_id).update(**update_data).exec()
            new_alert('Выпуск успешно сохранён', 'success')
            return redirect(url_for('issue_edit', issue_id=issue_id))

    if issue_id == 0:
        issue = {
            'id': 0,
            'title': '',
            'title_uz': '',
            'title_ru': '',
            'vol_no': '',
            'issue_no': '',
            'year': '',
            'category': '',
            'shortinfo': '',
            'shortinfo_uz': '',
            'shortinfo_ru': '',
            'price': '',
            'price_uz': '',
            'price_ru': '',
            'subscription_enable': False,
            'is_paid': False,
            'cover_image': '',
            'created_at': None
        }
    else:
        issue = db.issues.all().equal(id=issue_id).exec()
        if not issue:
            return 'Выпуск не найден', 404
        issue = issue[0]

    issue_categories = db.fix_issue_categories.get().exec()
    return render_template('website/issues/edit.html', issue=issue, issue_categories = issue_categories)



@bp.route('/fmadmin/website/articles')
@is_allowed
def articles():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    # Получаем значения фильтров
    search_title = request.args.get('title', '').strip()
    search_author = request.args.get('author', '').strip()
    search_orcid = request.args.get('orcid', '').strip()
    search_orcid_by_name = request.args.get('search_orcid_by_name', '')
    search_issue = request.args.get('issue', '').strip()

    # Получаем всех авторов и строим карту id/ORCID/имя
    authors = db.author_profile.all().exec()
    authors_map = {a['id']: a for a in authors}
    orcid_to_id = {a['orcid']: a['id'] for a in authors if a['orcid']}
    name_to_id = {a['name']: a['id'] for a in authors if a['name']}

    # Получаем все выпуски
    issues = db.issues.all().exec()
    issues_map = {i['id']: i for i in issues}

    # Формируем запрос к публикациям
    query = db.publications.all()
    if search_title:
        query = query.like(title=search_title)
    if search_issue:
        try:
            query = query.equal(issue_id=int(search_issue))
        except Exception:
            pass
    # Фильтр по автору (по имени или id)
    if search_author:
        author_ids = [aid for name, aid in name_to_id.items() if search_author.lower() in name.lower()]
        if author_ids:
            query = query.any(main_author_id=author_ids)
        else:
            query = query.any(main_author_id=[-1])
    # Фильтр по ORCID
    if search_orcid:
        if search_orcid_by_name:
            # Поиск по полному имени в поле ORCID
            author_ids = [aid for name, aid in name_to_id.items() if search_orcid.lower() in name.lower()]
            if author_ids:
                query = query.any(main_author_id=author_ids)
            else:
                query = query.any(main_author_id=[-1])
        else:
            # Обычный поиск по ORCID
            author_id = orcid_to_id.get(search_orcid)
            if author_id:
                query = query.any(main_author_id=[author_id])
            else:
                query = query.any(main_author_id=[-1])

    total_articles = query.copy().count().exec()
    articles = query.per_page(per_page).page(page).exec()
    total_pages = (total_articles + per_page - 1) // per_page

    # Формируем query_string для пагинации (без page)
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)

    return render_template('website/articles/articles.html', articles=articles, authors_map=authors_map, issues_map=issues_map,
                           page=page, total_articles=total_articles, total_pages=total_pages,
                           search_title=search_title, search_author=search_author, search_orcid=search_orcid, search_orcid_by_name=search_orcid_by_name, search_issue=search_issue,
                           issues=issues, pagination_query_string=pagination_query_string)

@bp.route('/fmadmin/website/articles/<int:article_id>', methods=['GET', 'POST'])
@is_allowed
def article_edit(article_id):
    if request.method == 'POST':        
        title = request.form.get('title')
        title_uz = request.form.get('title_uz')
        title_ru = request.form.get('title_ru')
        abstract = request.form.get('abstract')
        abstract_uz = request.form.get('abstract_uz')
        abstract_ru = request.form.get('abstract_ru')
        keywords = request.form.get('keywords')
        if keywords:
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        else:
            keywords = []

        keywords_uz = request.form.get('keywords_uz')
        if keywords_uz:
            keywords_uz = [k.strip() for k in keywords_uz.split(',') if k.strip()]
        else:
            keywords_uz = []

        keywords_ru = request.form.get('keywords_ru')
        if keywords_ru:
            keywords_ru = [k.strip() for k in keywords_ru.split(',') if k.strip()]
        else:
            keywords_ru = []
        additional = request.form.get('additional')
        main_author_id = request.form.get('main_author_id') or None
        subauthor_ids = request.form.getlist('subauthor_ids')
        subauthor_ids = [int(i) for i in subauthor_ids if i]
        issue_id = request.form.get('issue_id') or None
        doi = request.form.get('doi')
        doi_link = request.form.get('doi_link')
        date_sent = parse_date(request.form.get('date_sent'), with_time=True)
        date_accept = parse_date(request.form.get('date_accept'), with_time=True)
        date_publish = parse_date(request.form.get('date_publish'), with_time=True)
        comments = request.form.get('comments')
        # Обработка загруженных PDF файлов
        file_ids = []

        # Получаем существующие file_ids если они есть
        existing_file_ids = request.form.get('file_ids')
        if existing_file_ids:
            file_ids = [int(f.strip()) for f in existing_file_ids.split(',') if f.strip().isdigit()]

        # Обрабатываем новые загруженные файлы
        uploaded_files = request.files.getlist('pdf_files')
        for file in uploaded_files:
            if file and file.filename and file.filename.lower().endswith('.pdf'):
                try:
                    file_id = save_file_to_db(file, 'articles', f'PDF для статьи {article_id}')
                    if file_id:
                        file_ids.append(file_id)
                except Exception as e:
                    new_alert(f'Ошибка загрузки файла {file.filename}: {str(e)}', 'danger')
        is_paid = bool(request.form.get('is_paid'))
        price = request.form.get('price', 0, float)
        price_uz = request.form.get('price_uz', 0, float)
        price_ru = request.form.get('price_ru', 0, float)
        subscription_enable = bool(request.form.get('subscription_enable'))
        created_at = parse_date(request.form.get('created_at'), with_time=True)
        
        if article_id == 0:
            print("title", title)
            print("title_uz", title_uz)
            print("title_ru", title_ru)
            print("abstract", abstract)
            print("abstract_uz", abstract_uz)
            print("abstract_ru", abstract_ru)
            print("keywords", keywords)
            print("keywords_uz", keywords_uz)
            print("keywords_ru", keywords_ru)
            print("additional", additional)
            print("main_author_id", main_author_id)
            print("subauthor_ids", subauthor_ids)
            print("issue_id", issue_id)
            print("doi", doi)
            print("doi_link", doi_link)
            print("date_sent", date_sent)
            print("date_accept", date_accept)
            print("date_publish", date_publish)
            print("comments", comments)
            print("file_ids", file_ids)
            print("is_paid", is_paid)
            print("price", price)
            print("price_uz", price_uz)
            print("price_ru", price_ru)
            print("subscription_enable", subscription_enable)
            article_id_new = db.publications.add(
                title=title,
                title_uz=title_uz,
                title_ru=title_ru,
                abstract=abstract,
                abstract_uz=abstract_uz,
                abstract_ru=abstract_ru,
                keywords=keywords,
                keywords_uz=keywords_uz,
                keywords_ru=keywords_ru,
                additional=additional,
                main_author_id=main_author_id,
                subauthor_ids=subauthor_ids,
                issue_id=issue_id,
                doi=doi,
                doi_link=doi_link,
                date_sent=date_sent,
                date_accept=date_accept,
                date_publish=date_publish,
                comments=comments,
                file_ids=file_ids,
                is_paid=is_paid,
                price=price,
                price_uz=price_uz,
                price_ru=price_ru,
                subscription_enable=subscription_enable,
                current_views = 0,
                created_at=created_at or int(datetime.datetime.now().timestamp())
            ).exec()
            new_alert('Статья успешно создана', 'success')
            return redirect(url_for('article_edit', article_id=article_id_new[0]['id']))
        else:
            db.publications.all().equal(id=article_id).update(
                title=title,
                title_uz=title_uz,
                title_ru=title_ru,
                abstract=abstract,
                abstract_uz=abstract_uz,
                abstract_ru=abstract_ru,
                keywords=keywords,
                keywords_uz=keywords_uz,
                keywords_ru=keywords_ru,
                additional=additional,
                main_author_id=main_author_id,
                subauthor_ids=subauthor_ids,
                issue_id=issue_id,
                doi=doi,
                doi_link=doi_link,
                date_sent=date_sent,
                date_accept=date_accept,
                date_publish=date_publish,
                comments=comments,
                file_ids=file_ids,
                is_paid=is_paid,
                price=price,
                price_uz=price_uz,
                price_ru=price_ru,
                subscription_enable=subscription_enable,
                created_at=created_at
            ).exec()
            new_alert('Статья успешно сохранена', 'success')
            return redirect(url_for('article_edit', article_id=article_id))

    if article_id == 0:
        article = {
            'id': 0,
            'title': '',
            'title_uz': '',
            'title_ru': '',
            'abstract': '',
            'abstract_uz': '',
            'abstract_ru': '',
            'keywords': [],
            'keywords_uz': [],
            'keywords_ru': [],
            'additional': '',
            'main_author_id': None,
            'subauthor_ids': [],
            'issue_id': None,
            'doi': '',
            'doi_link': '',
            'date_sent': None,
            'date_accept': None,
            'date_publish': None,
            'comments': '',
            'file_ids': [],
            'is_paid': False,
            'price': '',
            'price_uz': '',
            'price_ru': '',
            'subscription_enable': False,
            'created_at': None
        }
    else:
        article = db.publications.all().equal(id=article_id).exec()
        if not article:
            return 'Статья не найдена', 404
        article = article[0]
    authors = db.author_profile.all().exec()
    issues = db.issues.all().exec()
    return render_template('website/articles/edit.html', article=article, authors=authors, issues=issues)

@bp.route('/fmadmin/website/articles/<int:article_id>/content', methods=['GET', 'POST'])
@is_allowed
def article_content(article_id):
    if request.method == 'POST':
        move_block_id = request.form.get('move_block_id')
        move_dir = request.form.get('move_dir')
        if move_block_id and move_dir:
            # Получить все блоки с order_id
            parts = db.publication_parts.all().equal(publication_id=article_id).order_by('order_id').exec()
            figures = db.publication_figures.all().equal(publication_id=article_id).order_by('order_id').exec()
            blocks = []
            for p in parts:
                blocks.append({'id': p['id'], 'order_id': p.get('order_id', 0), 'table': 'publication_parts'})
            for f in figures:
                blocks.append({'id': f['id'], 'order_id': f.get('order_id', 0), 'table': 'publication_figures'})
            blocks.sort(key=lambda x: x['order_id'])
            idx = next((i for i, b in enumerate(blocks) if str(b['id']) == str(move_block_id)), None)
            if idx is not None:
                if move_dir == 'up' and idx > 0:
                    a, b = blocks[idx], blocks[idx-1]
                elif move_dir == 'down' and idx < len(blocks)-1:
                    a, b = blocks[idx], blocks[idx+1]
                else:
                    return redirect(url_for('article_content', article_id=article_id))
                # Поменять order_id местами
                db.__getattr__(a['table']).all().equal(id=a['id']).update(order_id=b['order_id']).exec()
                db.__getattr__(b['table']).all().equal(id=b['id']).update(order_id=a['order_id']).exec()
            return redirect(url_for('article_content', article_id=article_id))
        delete_block_id = request.form.get('delete_block_id')
        if delete_block_id:
            db.publication_parts.all().equal(id=delete_block_id).delete().exec()
            db.publication_figures.all().equal(id=delete_block_id).delete().exec()
            return redirect(url_for('article_content', article_id=article_id))
        block_id = request.form.get('block_id')
        block_type = request.form.get('block_type')
        block_title = request.form.get('block_title')
        if block_type == 'text':
            block_text = request.form.get('block_text')
            if block_id:
                db.publication_parts.all().equal(id=block_id).update(
                    title=block_title,
                    content=block_text
                ).exec()
            else:
                max_order = 0
                parts = db.publication_parts.all().equal(publication_id=article_id).exec()
                figures = db.publication_figures.all().equal(publication_id=article_id).exec()
                for p in parts:
                    if p.get('order_id', 0) > max_order:
                        max_order = p.get('order_id', 0)
                for f in figures:
                    if f.get('order_id', 0) > max_order:
                        max_order = f.get('order_id', 0)
                db.publication_parts.add(
                    publication_id=article_id,
                    title=block_title,
                    content=block_text,
                    order_id=max_order + 1,
                    created_at=int(datetime.datetime.now().timestamp())
                ).exec()
        elif block_type == 'image':
            file = request.files.get('block_image')
            image_desc = request.form.get('block_image_desc')
            filepath = None
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                filename = f'{uuid.uuid4().hex}.{ext}'
                rel_dir = f'static/uploads/figures/{datetime.datetime.now().year}/{datetime.datetime.now().month:02d}'
                abs_dir = os.path.join(settings.SAVE_PATH, rel_dir)
                os.makedirs(abs_dir, exist_ok=True)
                file_path = os.path.join(abs_dir, filename)
                file.save(file_path)
                filepath = f'/{rel_dir}/{filename}'
            if block_id:
                db.publication_figures.all().equal(id=block_id).update(
                    title=image_desc,
                    filepath=filepath if filepath else None
                ).exec()
            else:
                max_order = 0
                parts = db.publication_parts.all().equal(publication_id=article_id).exec()
                figures = db.publication_figures.all().equal(publication_id=article_id).exec()
                for p in parts:
                    if p.get('order_id', 0) > max_order:
                        max_order = p.get('order_id', 0)
                for f in figures:
                    if f.get('order_id', 0) > max_order:
                        max_order = f.get('order_id', 0)
                db.publication_figures.add(
                    publication_id=article_id,
                    title=image_desc,
                    filepath=filepath,
                    order_id=max_order + 1,
                    created_at=int(datetime.datetime.now().timestamp())
                ).exec()
        elif block_type == 'table':
            pass
        return redirect(url_for('article_content', article_id=article_id))
    # GET: собрать контент из двух таблиц
    parts = db.publication_parts.all().equal(publication_id=article_id).order_by('order_id').exec()
    figures = db.publication_figures.all().equal(publication_id=article_id).order_by('order_id').exec()
    content_list = []
    for p in parts:
        content_list.append({'id': p.get('id'), 'type': 'text', 'title': p.get('title', ''), 'text': p.get('content', ''), 'order_id': p.get('order_id', 0)})
    for f in figures:
        content_list.append({'id': f.get('id'), 'type': 'image', 'image': f.get('filepath', ''), 'image_desc': f.get('title', ''), 'order_id': f.get('order_id', 0)})
    content_list.sort(key=lambda x: x.get('order_id', 0))
    article = db.publications.all().equal(id=article_id).exec()
    article = article[0] if article else None
    return render_template('website/articles/content.html', article_id=article_id, content_list=content_list, article=article)

@bp.route('/fmadmin/website/news')
@is_allowed
def news():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = db.news.all().equal(type='news')
    total_news = query.copy().count().exec()
    news_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_news + per_page - 1) // per_page
    # Формируем query_string для пагинации (без page)
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    return render_template('website/news/news.html', news_list=news_list, page=page, total_news=total_news, total_pages=total_pages, pagination_query_string=pagination_query_string)

@bp.route('/fmadmin/website/announcements')
def announcements():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = db.news.all().equal(type='announcement')
    total_announcements = query.copy().count().exec()
    announcements_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_announcements + per_page - 1) // per_page
    # Формируем query_string для пагинации (без page)
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    return render_template('website/announcements.html', announcements_list=announcements_list, page=page, total_announcements=total_announcements, total_pages=total_pages, pagination_query_string=pagination_query_string)

@bp.route('/fmadmin/website/tariffs')
def tariffs():
    tariffs = db.tariffs.all().exec()
    # Считаем количество пользователей на каждом тарифе
    users = db.users.all().exec()
    tariffs_user_count = {}
    for t in tariffs:
        tariffs_user_count[t['id']] = sum(1 for u in users if u.get('tariff_id') == t['id'])
    return render_template('website/tariffs.html', tariffs=tariffs, tariffs_user_count=tariffs_user_count)

@bp.route('/fmadmin/website/translations')
@is_allowed
def translations():
    search = request.args.get('search', '').strip()
    query = db.translations.all()
    translations = query.exec()
    if search:
        search_lower = search.lower()
        translations = [t for t in translations if search_lower in (t.get('alias') or '').lower() or search_lower in (t.get('content') or '').lower() or search_lower in (t.get('content_uz') or '').lower() or search_lower in (t.get('content_ru') or '').lower()]
    return render_template('website/translations.html', translations=translations, search=search)

@bp.route('/fmadmin/website/news/edit/<int:news_id>', methods=['GET', 'POST'])
def news_edit(news_id):
    if request.method == 'POST':
        title_ru = request.form.get('title_ru', '')
        title_uz = request.form.get('title_uz', '')
        title = request.form.get('title_en', '')
        content_ru = request.form.get('content_ru', '')
        content_uz = request.form.get('content_uz', '')
        content = request.form.get('content_en', '')
        status = request.form.get('status', 'draft')
        published_at = request.form.get('published_at')
        if published_at:
            published_at = int(datetime.datetime.strptime(published_at, '%Y-%m-%d').timestamp())
        else:
            published_at = None
        cover_image = None
        if 'cover_image' in request.files and request.files['cover_image'].filename:
            file = request.files['cover_image']
            ext = file.filename.rsplit('.', 1)[-1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            upload_folder = os.path.join(settings.SAVE_PATH, 'dist', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            cover_image = f"/static/uploads/{filename}"
        if news_id == 0:
            new_id = db.news.add(
                type='news',
                title=title,
                title_ru=title_ru,
                title_uz=title_uz,
                content=content,
                content_ru=content_ru,
                content_uz=content_uz,
                status=status,
                published_at=published_at,
                cover_image=cover_image,
                created_at=int(datetime.datetime.now().timestamp())
            ).exec()
            if isinstance(new_id, list):
                new_id = new_id[0]['id']
            elif isinstance(new_id, dict) and 'id' in new_id:
                new_id = new_id['id']
            return redirect(url_for('news_edit', news_id=new_id))
        else:
            news = {
                'id': news_id,
                'title': title,
                'title_ru': title_ru,
                'title_uz': title_uz,
                'content': content,
                'content_ru': content_ru,
                'content_uz': content_uz,
                'status': status,
                'published_at': published_at,
            }
            if cover_image:
                news['cover_image'] = cover_image
            _res = db.news.all().equal(id=news_id).update(**{k: v for k, v in news.items() if v is not None}).exec()
            if _res:
                flash('Новость успешно сохранена', 'success')
            else:
                flash('Ошибка при сохранении новости', 'danger')
            return redirect(url_for('news_edit', news_id=news_id))
    news = db.news.all().equal(id=news_id).exec()
    if not news and news_id != 0:
        return 'Новость не найдена', 404
    news = news[0] if news else {
        'id': 0,
        'title': '',
        'title_ru': '',
        'title_uz': '',
        'content': '',
        'content_ru': '',
        'content_uz': '',
        'status': 'draft',
        'published_at': None,
        'cover_image': ''
    }
    return render_template('website/news/news_edit.html', news_id=news_id, news=news)

@bp.route('/fmadmin/website/announcements/edit/<int:announcement_id>', methods=['GET', 'POST'])
def announcement_edit(announcement_id):
    if request.method == 'POST':
        title_ru = request.form.get('title_ru', '')
        title_uz = request.form.get('title_uz', '')
        title = request.form.get('title_en', '')
        content_ru = request.form.get('content_ru', '')
        content_uz = request.form.get('content_uz', '')
        content = request.form.get('content_en', '')
        status = request.form.get('status', 'draft')
        published_at = request.form.get('published_at')
        if published_at:
            published_at = int(datetime.datetime.strptime(published_at, '%Y-%m-%d').timestamp())
        else:
            published_at = None
        cover_image = None
        if 'cover_image' in request.files and request.files['cover_image'].filename:
            file = request.files['cover_image']
            ext = file.filename.rsplit('.', 1)[-1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            upload_folder = os.path.join(settings.SAVE_PATH, 'dist', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            cover_image = f"/static/uploads/{filename}"
        if announcement_id == 0:
            new_id = db.news.add(
                type='announcement',
                title=title,
                title_ru=title_ru,
                title_uz=title_uz,
                content=content,
                content_ru=content_ru,
                content_uz=content_uz,
                status=status,
                published_at=published_at,
                cover_image=cover_image,
                created_at=int(datetime.datetime.now().timestamp())
            ).exec()
            if isinstance(new_id, list):
                new_id = new_id[0]['id']
            elif isinstance(new_id, dict) and 'id' in new_id:
                new_id = new_id['id']
            return redirect(url_for('announcement_edit', announcement_id=new_id))
        else:
            announcement = {
                'id': announcement_id,
                'title': title,
                'title_ru': title_ru,
                'title_uz': title_uz,
                'content': content,
                'content_ru': content_ru,
                'content_uz': content_uz,
                'status': status,
                'published_at': published_at,
            }
            if cover_image:
                announcement['cover_image'] = cover_image
            _res = db.news.all().equal(id=announcement_id).update(**{k: v for k, v in announcement.items() if v is not None}).exec()
            if _res:
                flash('Объявление успешно сохранено', 'success')
            else:
                flash('Ошибка при сохранении объявления', 'danger')
            return redirect(url_for('announcement_edit', announcement_id=announcement_id))
    announcement = db.news.all().equal(id=announcement_id).exec()
    if not announcement and announcement_id != 0:
        return 'Объявление не найдено', 404
    announcement = announcement[0] if announcement else {
        'id': 0,
        'title': '',
        'title_ru': '',
        'title_uz': '',
        'content': '',
        'content_ru': '',
        'content_uz': '',
        'status': 'draft',
        'published_at': None,
        'cover_image': ''
    }
    return render_template('website/announcements/announcement_edit.html', announcement_id=announcement_id, announcement=announcement)

@bp.route('/fmadmin/finance/payments')
@is_allowed
def payments():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', '').strip()
    
    # Получаем все платежи, исключая unpaid
    query = db.payments.all().unequal(status='unpaid')
    
    # Фильтр по статусу
    if status_filter and status_filter in ['pending', 'paid', 'rejected']:
        query = query.equal(status=status_filter)
    
    total_payments = query.copy().count().exec()
    payments_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_payments + per_page - 1) // per_page
    
    # Формируем query_string для пагинации
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    
    # Получаем пользователей для отображения имен
    users = db.users.all().exec()
    users_map = {u['id']: u for u in users}
    
    return render_template('finance/payments.html', 
                         payments_list=payments_list, 
                         page=page, 
                         total_payments=total_payments, 
                         total_pages=total_pages, 
                         pagination_query_string=pagination_query_string,
                         status_filter=status_filter,
                         users_map=users_map)

@bp.route('/fmadmin/finance/payments/edit', methods=['POST'])
@is_allowed
def payment_edit():
    try:
        payment_id = request.form.get('payment_id')
        status = request.form.get('status')
        amount = request.form.get('amount')
        comment = request.form.get('comment', '')
        
        if not payment_id or not status or not amount:
            return jsonify({'success': False, 'error': 'Не все обязательные поля заполнены'})
        
        # Обновляем платеж
        update_data = {
            'status': status,
            'amount': float(amount)
        }
        
        if comment:
            update_data['comment'] = comment
        
        result = db.payments.all().equal(id=int(payment_id)).update(**update_data).exec()
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Платеж не найден'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/static/<path:filename>')
def serve_static_any(filename):
    return send_from_directory(os.path.join(settings.SAVE_PATH, 'static'), filename)

@bp.route('/fmadmin/submissions')
@is_allowed
def submissions():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', '').strip()
    user_filter = request.args.get('user', '').strip()
    
    # Получаем все подачи
    query = db.submissions.all()
    
    # Исключаем черновики
    query = query.unequal(status='draft')
    
    # Фильтр по статусу
    if status_filter:
        query = query.equal(status=status_filter)
    
    # Фильтр по пользователю
    if user_filter:
        try:
            query = query.equal(user_id=int(user_filter))
        except:
            pass
    
    total_submissions = query.copy().count().exec()
    submissions_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_submissions + per_page - 1) // per_page
    
    # Формируем query_string для пагинации
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    
    # Получаем пользователей и авторов для отображения имен
    users = db.users.all().exec()
    users_map = {u['id']: u for u in users}
    
    authors = db.author_profile.all().exec()
    authors_map = {a['id']: a for a in authors}
    
    return render_template('submissions/list.html', 
                         submissions_list=submissions_list, 
                         page=page, 
                         total_submissions=total_submissions, 
                         total_pages=total_pages, 
                         pagination_query_string=pagination_query_string,
                         status_filter=status_filter,
                         user_filter=user_filter,
                         users_map=users_map,
                         authors_map=authors_map)

@bp.route('/fmadmin/submissions/<int:submission_id>')
@is_allowed
def submission_detail(submission_id):
    submission = db.submissions.all().equal(id=submission_id).exec()
    if not submission:
        return 'Подача не найдена', 404
    submission = submission[0]
    
    # Получаем данные пользователя
    user = None
    if submission.get('user_id'):
        user_data = db.users.all().equal(id=submission['user_id']).exec()
        if user_data:
            user = user_data[0]
    
    # Получаем данные авторов
    main_author = None
    if submission.get('main_author_id'):
        author_data = db.author_profile.all().equal(id=submission['main_author_id']).exec()
        if author_data:
            main_author = author_data[0]
    
    sub_authors = []
    if submission.get('sub_author_ids'):
        sub_authors = db.author_profile.all().any(id=submission['sub_author_ids']).exec()
    
    return render_template('submissions/detail.html', 
                         submission=submission, 
                         user=user, 
                         main_author=main_author, 
                         sub_authors=sub_authors)

@bp.route('/fmadmin/submissions/documents')
@is_allowed
def submission_documents():
    page = request.args.get('page', 1, type=int)
    per_page = 25
    status_filter = request.args.get('status', '').strip()
    search_title = request.args.get('title', '').strip()
    user_filter = request.args.get('user', '').strip()
    
    # Получаем документы из user_doc_uploads
    query = db.user_doc_uploads.all()
    
    # Фильтр по статусу верификации
    if status_filter and status_filter in ['verified', 'pending', 'rejected']:
        query = query.equal(verification_status=status_filter)
    
    # Поиск по названию работы
    if search_title:
        query = query.like(work_title=search_title)
    
    # Фильтр по пользователю
    if user_filter:
        try:
            query = query.equal(user_id=int(user_filter))
        except:
            pass
    
    total_docs = query.copy().count().exec()
    docs_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_docs + per_page - 1) // per_page
    
    # Формируем query_string для пагинации
    args_for_pagination = {k: v for k, v in request.args.items() if k != 'page' and v}
    pagination_query_string = ''
    if args_for_pagination:
        pagination_query_string = '&' + urlencode(args_for_pagination)
    
    # Получаем пользователей для отображения имен
    users = db.users.all().exec()
    users_map = {u['id']: u for u in users}
    
    return render_template('submissions/documents.html', 
                         docs_list=docs_list, 
                         page=page, 
                         total_docs=total_docs, 
                         total_pages=total_pages, 
                         pagination_query_string=pagination_query_string,
                         status_filter=status_filter,
                         search_title=search_title,
                         user_filter=user_filter,
                         users_map=users_map)

@bp.route('/fmadmin/submissions/edit', methods=['POST'])
@is_allowed
def submission_edit():
    try:
        submission_id = request.form.get('submission_id')
        status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        if not submission_id or not status:
            return jsonify({'success': False, 'error': 'Не все обязательные поля заполнены'})
        
        # Обновляем подачу
        update_data = {
            'status': status,
            'notes': notes,
            'updated_at': int(datetime.datetime.now().timestamp())
        }
        
        result = db.submissions.all().equal(id=int(submission_id)).update(**update_data).exec()
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Подача не найдена'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/fmadmin/submissions/documents/edit', methods=['POST'])
@is_allowed
def document_edit():
    try:
        doc_id = request.form.get('doc_id')
        verification_status = request.form.get('verification_status')
        
        if not doc_id or not verification_status:
            return jsonify({'success': False, 'error': 'Не все обязательные поля заполнены'})
        
        # Обновляем документ
        update_data = {
            'verification_status': verification_status,
            'updated_at': int(datetime.datetime.now().timestamp())
        }
        
        result = db.user_doc_uploads.all().equal(id=int(doc_id)).update(**update_data).exec()
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Документ не найден'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== РЕДАКТОРЫ ====================

@bp.route('/fmadmin/editors')
@is_allowed
def editors():
    """Список всех редакторов"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_name = request.args.get('name', '').strip()
    search_specialization = request.args.get('specialization', '').strip()

    query = db.users.all().equal(rolename='editor')
    if search_name:
        query = query.like(name=search_name)
    if search_specialization:
        query = query.like(editor_specialization=search_specialization)

    total_editors = query.copy().count().exec()
    editors_list = query.per_page(per_page).page(page).exec()
    total_pages = (total_editors + per_page - 1) // per_page

    # Получаем статистику по назначениям для каждого редактора
    try:
        assignments = db.editor_assignments.all().exec()
    except:
        assignments = []

    editor_stats = {}
    for editor in editors_list:
        editor_assignments = [a for a in assignments if a.get('editor_id') == editor.get('id')]
        editor_stats[editor.get('id')] = {
            'total': len(editor_assignments),
            'pending': len([a for a in editor_assignments if a.get('status') == 'pending']),
            'reviewed': len([a for a in editor_assignments if a.get('status') == 'reviewed']),
            'rejected': len([a for a in editor_assignments if a.get('status') == 'rejected'])
        }

    return render_template('editors/editors.html',
                         editors=editors_list,
                         page=page,
                         total_editors=total_editors,
                         total_pages=total_pages,
                         search_name=search_name,
                         search_specialization=search_specialization,
                         editor_stats=editor_stats)

@bp.route('/fmadmin/editors/<int:editor_id>', methods=['GET', 'POST'])
@is_allowed
def editor_edit(editor_id):
    """Редактирование редактора"""
    if request.method == 'POST':
        if editor_id == 0:
            # Создание нового редактора
            name = request.form.get('name')
            second_name = request.form.get('second_name')
            father_name = request.form.get('father_name')
            email = request.form.get('email')
            editor_specialization = request.form.get('editor_specialization')
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(password) if password else None

            editor_id_new = db.users.add(
                name=name,
                second_name=second_name,
                father_name=father_name,
                email=email,
                rolename='editor',
                editor_specialization=editor_specialization,
                password=hashed_password,
                created_at=int(datetime.datetime.now().timestamp()),
                register_time=int(datetime.datetime.now().timestamp())
            ).exec()
            new_alert('Редактор успешно создан', 'success')
            return redirect(url_for('editor_edit', editor_id=editor_id_new))
        else:
            # Обновление существующего редактора
            data = request.json if request.is_json else request.form
            db.users.all().equal(id=editor_id).update(
                name=data.get('name'),
                second_name=data.get('second_name'),
                father_name=data.get('father_name'),
                email=data.get('email'),
                editor_specialization=data.get('editor_specialization')
            ).exec()
            new_alert('Редактор успешно сохранён', 'success')
            return redirect(url_for('editor_edit', editor_id=editor_id))

    if editor_id == 0:
        # Новый редактор
        editor = {
            'id': 0,
            'name': '',
            'second_name': '',
            'father_name': '',
            'email': '',
            'editor_specialization': '',
            'rolename': 'editor'
        }
        password = uuid.uuid4().hex
        return render_template('editors/edit.html', editor=editor, password=password)
    else:
        editor = db.users.all().equal(id=editor_id).equal(rolename='editor').exec()
        if not editor:
            return 'Редактор не найден', 404
        editor = editor[0]

        # Получаем назначения редактора
        try:
            editor_assignments = db.editor_assignments.all().equal(editor_id=editor_id).exec()
        except:
            editor_assignments = []

        # Получаем статистику
        editor_stats = {
            'total': len(editor_assignments),
            'pending': len([a for a in editor_assignments if a.get('status') == 'pending']),
            'reviewed': len([a for a in editor_assignments if a.get('status') == 'reviewed']),
            'rejected': len([a for a in editor_assignments if a.get('status') == 'rejected'])
        }

        # Получаем информацию о статьях
        submission_ids = [a.get('submission_id') for a in editor_assignments if a.get('submission_id')]
        submissions = []
        if submission_ids:
            try:
                submissions = db.submissions.all().exec()
            except:
                submissions = []

        submissions_map = {s.get('id'): s for s in submissions if s.get('id')}

        return render_template('editors/edit.html',
                             editor=editor,
                             editor_assignments=editor_assignments,
                             editor_stats=editor_stats,
                             submissions_map=submissions_map)

@bp.route('/fmadmin/editor-assignments')
@is_admin_or_editor
def editor_assignments():
    """Список назначений для редакторов"""
    current_user = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', '').strip()
    editor_filter = request.args.get('editor', '').strip()
    submission_id_filter = request.args.get('submission_id', '').strip()
    submission_title_filter = request.args.get('submission_title', '').strip()

    query = db.editor_assignments.all()

    # Если текущий пользователь - редактор, показываем только его назначения
    if current_user.get('rolename') == 'editor':
        query = query.equal(editor_id=current_user['id'])

    if status_filter:
        query = query.equal(status=status_filter)
    if editor_filter:
        try:
            query = query.equal(editor_id=int(editor_filter))
        except ValueError:
            pass

    # Получаем все назначения для фильтрации по статьям
    try:
        all_assignments = query.exec()
    except:
        all_assignments = []

    # Получаем все статьи для фильтрации
    try:
        all_submissions = db.submissions.all().exec()
    except:
        all_submissions = []

    submissions_map = {s.get('id'): s for s in all_submissions if s.get('id')}

    # Фильтрация по ID статьи
    if submission_id_filter:
        try:
            submission_id = int(submission_id_filter)
            all_assignments = [a for a in all_assignments if a.get('submission_id') == submission_id]
        except ValueError:
            pass

    # Фильтрация по названию статьи
    if submission_title_filter:
        filtered_assignments = []
        for assignment in all_assignments:
            submission = submissions_map.get(assignment.get('submission_id'))
            if submission and submission_title_filter.lower() in submission.get('title', '').lower():
                filtered_assignments.append(assignment)
        all_assignments = filtered_assignments

    total_assignments = len(all_assignments)
    total_pages = (total_assignments + per_page - 1) // per_page

    # Пагинация
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    assignments_list = all_assignments[start_idx:end_idx]

    # Получаем связанные данные
    editors_list = get_editors()
    editors_map = {e.get('id'): e for e in editors_list if e.get('id')}

    try:
        users = db.users.all().exec()
    except:
        users = []
    users_map = {u.get('id'): u for u in users if u.get('id')}

    return render_template('editors/assignments.html',
                         assignments=assignments_list,
                         page=page,
                         total_assignments=total_assignments,
                         total_pages=total_pages,
                         status_filter=status_filter,
                         editor_filter=editor_filter,
                         submission_id_filter=submission_id_filter,
                         submission_title_filter=submission_title_filter,
                         submissions_map=submissions_map,
                         editors_map=editors_map,
                         users_map=users_map,
                         editors=editors_list,
                         current_user=current_user)

@bp.route('/fmadmin/submissions/<int:submission_id>/assign-editors', methods=['GET', 'POST'])
@is_allowed
def assign_editors(submission_id):
    """Назначение редакторов для проверки статьи"""
    if request.method == 'POST':
        editor_ids = request.form.getlist('editor_ids')
        current_user = get_current_user()

        # Проверяем, что статья существует
        submission = db.submissions.all().equal(id=submission_id).exec()
        if not submission:
            new_alert('Статья не найдена', 'danger')
            return redirect(url_for('submissions'))

        submission = submission[0]

        # Создаем назначения для выбранных редакторов
        for editor_id in editor_ids:
            try:
                editor_id = int(editor_id)
                # Проверяем, что редактор еще не назначен на эту статью
                existing = db.editor_assignments.all().equal(submission_id=submission_id).equal(editor_id=editor_id).exec()
                if not existing:
                    assignment_id = db.editor_assignments.add(
                        submission_id=submission_id,
                        editor_id=editor_id,
                        assigned_by=current_user['id'],
                        assigned_at=int(datetime.datetime.now().timestamp()),
                        status='pending'
                    ).exec()

                    # Создаем уведомление для редактора
                    create_editor_notification(
                        editor_id=editor_id,
                        assignment_id=assignment_id,
                        message=f'Вам назначена статья "{submission["title"]}" для проверки'
                    )
            except ValueError:
                continue

        # Обновляем статус статьи
        db.submissions.all().equal(id=submission_id).update(
            editor_review_status='assigned'
        ).exec()

        new_alert('Редакторы успешно назначены', 'success')
        return redirect(url_for('submissions'))

    # GET запрос - показываем форму назначения
    submission = db.submissions.all().equal(id=submission_id).exec()
    if not submission:
        return 'Статья не найдена', 404
    submission = submission[0]

    # Получаем всех редакторов
    editors_list = get_editors()

    # Получаем уже назначенных редакторов
    assigned_editors = db.editor_assignments.all().equal(submission_id=submission_id).exec()
    assigned_editor_ids = [a['editor_id'] for a in assigned_editors]

    return render_template('editors/assign.html',
                         submission=submission,
                         editors=editors_list,
                         assigned_editor_ids=assigned_editor_ids)

@bp.route('/fmadmin/editor-assignments/<int:assignment_id>/review', methods=['GET', 'POST'])
@is_editor_allowed
def review_assignment(assignment_id):
    """Страница проверки статьи редактором"""
    current_user = get_current_user()

    # Получаем назначение
    assignment = db.editor_assignments.all().equal(id=assignment_id).exec()
    if not assignment:
        return 'Назначение не найдено', 404
    assignment = assignment[0]

    # Проверяем права доступа
    if current_user.get('rolename') == 'editor' and assignment['editor_id'] != current_user['id']:
        return 'Доступ запрещен', 403

    if request.method == 'POST':
        editor_comment = request.form.get('editor_comment', '')
        status = request.form.get('status', 'reviewed')

        # Обработка загруженного файла
        editor_file = None
        if 'editor_file' in request.files and request.files['editor_file'].filename:
            file = request.files['editor_file']
            try:
                editor_file = save_file('editor_reviews', file, ['pdf', 'doc', 'docx', 'txt'])
            except ValueError as e:
                new_alert(str(e), 'danger')
                return redirect(url_for('review_assignment', assignment_id=assignment_id))

        # Обновляем назначение
        db.editor_assignments.all().equal(id=assignment_id).update(
            status=status,
            editor_comment=editor_comment,
            editor_file=editor_file,
            reviewed_at=int(datetime.datetime.now().timestamp())
        ).exec()

        # Обновляем статус статьи
        submission_id = assignment['submission_id']
        all_assignments = db.editor_assignments.all().equal(submission_id=submission_id).exec()

        # Проверяем, все ли редакторы завершили проверку
        all_reviewed = all(a['status'] in ['reviewed', 'rejected'] for a in all_assignments)
        if all_reviewed:
            db.submissions.all().equal(id=submission_id).update(
                editor_review_status='reviewed'
            ).exec()
        else:
            db.submissions.all().equal(id=submission_id).update(
                editor_review_status='in_review'
            ).exec()

        new_alert('Проверка сохранена', 'success')
        return redirect(url_for('editor_assignments'))

    # GET запрос - показываем форму проверки
    submission = db.submissions.all().equal(id=assignment['submission_id']).exec()
    if not submission:
        return 'Статья не найдена', 404
    submission = submission[0]

    return render_template('editors/review.html',
                         assignment=assignment,
                         submission=submission)

def register(app):
    app.register_blueprint(bp)
    # Add endpoint aliases without blueprint prefix for legacy templates (url_for('index'), etc.)
    for rule in list(app.url_map.iter_rules()):
        if not rule.endpoint.startswith('fmadmin_web.'):
            continue
        if not rule.rule.startswith('/fmadmin/'):
            continue
        alias = rule.endpoint.split('.', 1)[1]
        if alias == 'static' or alias in app.view_functions:
            continue
        app.add_url_rule(
            rule.rule,
            endpoint=alias,
            view_func=app.view_functions[rule.endpoint],
            methods=sorted(m for m in rule.methods if m not in {'HEAD', 'OPTIONS'}) or None
        )
