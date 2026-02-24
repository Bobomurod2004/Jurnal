# flake8: noqa
import os
import time
import uuid
import requests
from flask import request, jsonify
from werkzeug.utils import secure_filename
from extensions import db
from modules.translate import t, translate, clear_translations_cache
import settings


def get_translation(alias):
    translation = db.translations.get(alias=alias).exec()
    if translation:
        return jsonify({'success': True, 'translation': translation[0]})
    return jsonify({'success': False, 'message': 'Translation not found'}), 404


def update_translation(alias):
    data = request.get_json()
    content = data.get('content')
    content_ru = data.get('content_ru')
    content_uz = data.get('content_uz')

    translation = db.translations.get(alias=alias).exec()
    if translation:
        db.translations.get(alias=alias).update(
            content=content,
            content_ru=content_ru,
            content_uz=content_uz
        ).exec()
        clear_translations_cache()
        return jsonify({'success': True})

    db.translations.add(
        alias=alias,
        content=content,
        content_ru=content_ru,
        content_uz=content_uz,
        created_at=int(time.time())
    ).exec()
    clear_translations_cache()
    return jsonify({'success': True})


def sync_translations():
    """API endpoint для синхронизации переводов с mainweb"""
    try:
        mainweb_url = "http://localhost:16534"
        translations = db.translations.get().exec()
        translations_count = len(translations)

        api_url = f"{mainweb_url}/api/translations/clear_cache"
        response = requests.post(api_url, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': f'Кеш переводов очищен. Синхронизировано {translations_count} переводов.',
                    'translations_count': translations_count
                })
            msg = result.get("message", "Unknown error")
            return jsonify({
                'success': False,
                'message': f'Ошибка API mainweb: {msg}'
            })
        return jsonify({'success': False, 'message': f'HTTP ошибка: {response.status_code}'})

    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'message': f'Не удается подключиться к mainweb ({mainweb_url}). Убедитесь, что mainweb запущен.'
        })
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Таймаут при подключении к mainweb'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка синхронизации: {str(e)}'})


def create_tariff():
    data = request.get_json()
    db.tariffs.add(
        name=data.get('name'),
        name_uz=data.get('name_uz'),
        name_ru=data.get('name_ru'),
        description=data.get('description'),
        description_uz=data.get('description_uz'),
        description_ru=data.get('description_ru'),
        price_rub=data.get('price_rub', 0),
        price_uzs=data.get('price_uzs', 0),
        price_usd=data.get('price_usd', 0),
        user_limit=data.get('user_limit', 0),
        is_default=data.get('is_default', False),
        is_verified=data.get('is_verified', False),
        created_at=data.get('created_at') or int(time.time()),
        updated_at=data.get('updated_at') or int(time.time())
    ).exec()

    return jsonify({'success': True})


def update_tariff(tariff_id):
    data = request.get_json()
    db.tariffs.get(id=tariff_id).update(
        name=data.get('name'),
        name_uz=data.get('name_uz'),
        name_ru=data.get('name_ru'),
        description=data.get('description'),
        description_uz=data.get('description_uz'),
        description_ru=data.get('description_ru'),
        price_rub=data.get('price_rub', 0),
        price_uzs=data.get('price_uzs', 0),
        price_usd=data.get('price_usd', 0),
        user_limit=data.get('user_limit', 0),
        is_default=data.get('is_default', False),
        is_verified=data.get('is_verified', False),
        updated_at=data.get('updated_at') or int(time.time())
    ).exec()
    return jsonify({'success': True})


def delete_tariff(tariff_id):
    try:
        tariff = db.tariffs.get(id=tariff_id).exec()
        if not tariff:
            return jsonify({'success': False, 'error': 'Тариф не найден'}), 404

        tariff = tariff[0]
        if tariff.get('is_default', False):
            return jsonify({'success': False, 'error': 'Нельзя удалить тариф по умолчанию'}), 400

        users_with_tariff = db.users.get(tariff_id=tariff_id).exec()
        if users_with_tariff:
            db.users.get(tariff_id=tariff_id).update(
                tariff_id=None,
                subscription_end_date=None
            ).exec()

        db.tariffs.get(id=tariff_id).delete().exec()
        return jsonify({
            'success': True,
            'message': f'Тариф удален. {len(users_with_tariff)} пользователей переведены на обычный режим.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def upload_image():
    file = None
    if 'upload' in request.files:
        file = request.files['upload']
    elif 'image' in request.files:
        file = request.files['image']

    if not file:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
        return jsonify({'success': False, 'message': 'Invalid file type'})

    new_filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(settings.SAVE_PATH, 'static', 'uploads', 'images')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, new_filename)
    file.save(file_path)

    return jsonify({'success': True, 'url': f"/static/uploads/images/{new_filename}"})


def get_publication_refs():
    refs = db.publication_refs.get().exec()
    return jsonify({'success': True, 'refs': refs})


def create_publication_ref():
    data = request.get_json()
    result = db.publication_refs.add(**data).exec()
    return jsonify({'success': True, 'ref': result[0] if result else None})


def get_article_references(article_id):
    refs = db.publication_refs.get(publication_id=article_id).exec()
    return jsonify({'success': True, 'refs': refs})


def get_article_citations(article_id):
    citations = db.publication_citations.get(publication_id=article_id).exec()
    return jsonify({'success': True, 'citations': citations})


def create_reference():
    data = request.get_json()
    result = db.references.add(**data).exec()
    return jsonify({'success': True, 'reference': result[0] if result else None})


def get_reference(reference_id):
    ref = db.references.get(id=reference_id).exec()
    if not ref:
        return jsonify({'success': False, 'message': 'Reference not found'}), 404
    return jsonify({'success': True, 'reference': ref[0]})


def update_reference(reference_id):
    data = request.get_json()
    db.references.get(id=reference_id).update(**data).exec()
    ref = db.references.get(id=reference_id).exec()
    return jsonify({'success': True, 'reference': ref[0] if ref else None})


def delete_reference(reference_id):
    db.references.get(id=reference_id).delete().exec()
    return jsonify({'success': True})


def search_references():
    search = request.args.get('search', '').strip()
    if not search:
        return jsonify({'success': True, 'references': []})

    refs = db.references.get().like(title=search).exec()
    return jsonify({'success': True, 'references': refs})


def create_citation():
    data = request.get_json()
    result = db.publication_citations.add(**data).exec()
    return jsonify({'success': True, 'citation': result[0] if result else None})


def get_citation(citation_id):
    citation = db.publication_citations.get(id=citation_id).exec()
    if not citation:
        return jsonify({'success': False, 'message': 'Citation not found'}), 404
    return jsonify({'success': True, 'citation': citation[0]})


def update_citation(citation_id):
    data = request.get_json()
    db.publication_citations.get(id=citation_id).update(**data).exec()
    citation = db.publication_citations.get(id=citation_id).exec()
    return jsonify({'success': True, 'citation': citation[0] if citation else None})


def delete_citation(citation_id):
    db.publication_citations.get(id=citation_id).delete().exec()
    return jsonify({'success': True})


def api_getauthor():
    data = request.get_json()
    orcid = data.get('orcid')
    name = data.get('name')

    if orcid:
        author_profile = db.author_profile.get(orcid=orcid).exec()
    else:
        author_profile = db.author_profile.get().like(name=name).exec()

    if not author_profile:
        return jsonify({'success': False, 'message': 'Author not found'})

    author_profile = author_profile[0]
    return jsonify({'success': True, 'author': author_profile})


def api_createauthor():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Name is required'})

    result = db.author_profile.add(
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
        created_at=int(time.time())
    ).exec()

    return jsonify({'success': True, 'author': result[0] if result else None})


def register(app):
    app.add_url_rule('/fmadmin/api/translation/<alias>', view_func=get_translation, methods=['GET'])
    app.add_url_rule('/fmadmin/api/translation/<alias>', view_func=update_translation, methods=['POST'])
    app.add_url_rule('/fmadmin/api/sync-translations', view_func=sync_translations, methods=['POST'])
    app.add_url_rule('/fmadmin/api/tariff', view_func=create_tariff, methods=['POST'])
    app.add_url_rule('/fmadmin/api/tariff/<int:tariff_id>', view_func=update_tariff, methods=['POST'])
    app.add_url_rule('/fmadmin/api/tariff/<int:tariff_id>/delete', view_func=delete_tariff, methods=['DELETE'])
    app.add_url_rule('/fmadmin/api/upload_image', view_func=upload_image, methods=['POST'])
    app.add_url_rule('/fmadmin/api/publication_refs', view_func=get_publication_refs)
    app.add_url_rule('/fmadmin/api/publication_refs', view_func=create_publication_ref, methods=['POST'])
    app.add_url_rule('/fmadmin/api/articles/<int:article_id>/references', view_func=get_article_references)
    app.add_url_rule('/fmadmin/api/articles/<int:article_id>/citations', view_func=get_article_citations)
    app.add_url_rule('/fmadmin/api/references', view_func=create_reference, methods=['POST'])
    app.add_url_rule('/fmadmin/api/references/<int:reference_id>', view_func=get_reference, methods=['GET'])
    app.add_url_rule('/fmadmin/api/references/<int:reference_id>', view_func=update_reference, methods=['PUT'])
    app.add_url_rule('/fmadmin/api/references/<int:reference_id>', view_func=delete_reference, methods=['DELETE'])
    app.add_url_rule('/fmadmin/api/references/search', view_func=search_references)
    app.add_url_rule('/fmadmin/api/citations', view_func=create_citation, methods=['POST'])
    app.add_url_rule('/fmadmin/api/citations/<int:citation_id>', view_func=get_citation, methods=['GET'])
    app.add_url_rule('/fmadmin/api/citations/<int:citation_id>', view_func=update_citation, methods=['PUT'])
    app.add_url_rule('/fmadmin/api/citations/<int:citation_id>', view_func=delete_citation, methods=['DELETE'])
    app.add_url_rule('/fmadmin/api/getauthor', view_func=api_getauthor, methods=['POST'])
    app.add_url_rule('/fmadmin/api/createauthor', view_func=api_createauthor, methods=['POST'])
