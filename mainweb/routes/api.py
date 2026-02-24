# flake8: noqa
import os
import time
from werkzeug.utils import secure_filename
from flask import request, jsonify, session
from extensions import dbc
from modules.translate import t, translate, clear_translations_cache
import settings
from utils.auth import login_required, is_valid_email
from utils.uploads import allowed_file
from werkzeug.security import generate_password_hash, check_password_hash


def app__api_getauthor():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json()
    search = data.get('search')

    if not search:
        return jsonify({'success': False, 'message': 'Required field missing: search'})

    if search.strip().isdigit():
        author_profile = dbc.author_profile.get(id=int(search.strip())).exec()
    else:
        author_profile = dbc.author_profile.get().like(name=search.strip()).exec()

    if not author_profile:
        return jsonify({'success': False, 'message': f'No author found for {search}'})

    author_profile = author_profile[0]
    return jsonify({
        'success': True,
        'author': {
            'id': author_profile['id'],
            'name': author_profile['name'],
            'organization': author_profile['organization'],
            'department': author_profile['department'],
            'position': author_profile['position'],
            'email': author_profile['email'],
            'phone': author_profile['phone'],
            'orcid': author_profile['orcid'],
            'address_street': author_profile['address_street'],
            'address_city': author_profile['address_city'],
            'address_country': author_profile['address_country'],
            'address_zip': author_profile['address_zip']
        }
    })


def app__api_getcurrentauthor():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    author_profile = dbc.author_profile.get(user_id=user_id).exec()
    if not author_profile:
        return jsonify({'success': False, 'message': 'No author profile found for current user'})

    author_profile = author_profile[0]
    return jsonify({
        'success': True,
        'author': {
            'id': author_profile['id'],
            'name': author_profile['name'],
            'organization': author_profile['organization'],
            'department': author_profile['department'],
            'position': author_profile['position'],
            'email': author_profile['email'],
            'phone': author_profile['phone'],
            'orcid': author_profile['orcid'],
            'address_street': author_profile['address_street'],
            'address_city': author_profile['address_city'],
            'address_country': author_profile['address_country'],
            'address_zip': author_profile['address_zip']
        }
    })


def app__api_getclassifications():
    classifications = dbc.fix_classifications.get().exec()
    return jsonify({'success': True, 'classifications': classifications})


def app__api_article_save():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json()
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission_id = data.get('submission_id')

    try:
        submission_data = {
            'user_id': user_id,
            'status': 'draft',
            'title': data.get('title'),
            'abstract': data.get('abstract'),
            'keywords': data.get('keywords', []),
            'classifications': data.get('classifications', []),
            'is_special': data.get('is_special', False),
            'is_dataset': data.get('is_dataset', False),
            'check_copyright': data.get('check_copyright', False),
            'check_ethical': data.get('check_ethical', False),
            'check_consent': data.get('check_consent', False),
            'check_acknowledgements': data.get('check_acknowledgements', False),
            'is_used_previous': data.get('is_used_previous', False),
            'word_count': data.get('word_count'),
            'is_corresponding_author': data.get('is_corresponding_author', False),
            'main_author_id': data.get('main_author_id'),
            'sub_author_ids': data.get('sub_author_ids', []),
            'is_competing_interests': data.get('is_competing_interests', False),
            'notes': data.get('notes'),
            'file_authors': data.get('file_authors'),
            'file_anonymized': data.get('file_anonymized'),
            'updated_at': int(time.time())
        }

        if submission_id:
            submission = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
            if not submission:
                return jsonify({'success': False, 'message': 'Submission not found'})

            dbc.submissions.get(id=submission_id).update(**submission_data).exec()
            return jsonify({'success': True, 'message': 'Draft updated successfully'})

        submission_data['created_date'] = int(time.time())
        result = dbc.submissions.add(**submission_data).exec()
        if result:
            return jsonify({'success': True, 'message': 'Draft saved successfully', 'submission_id': result[0]['id']})

        return jsonify({'success': False, 'message': 'Failed to save draft'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving draft: {str(e)}'})


def app__api_article_submit():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json()
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission_id = data.get('submission_id')

    try:
        submission_data = {
            'user_id': user_id,
            'status': 'submitted',
            'title': data.get('title'),
            'abstract': data.get('abstract'),
            'keywords': data.get('keywords', []),
            'classifications': data.get('classifications', []),
            'is_special': data.get('is_special', False),
            'is_dataset': data.get('is_dataset', False),
            'check_copyright': data.get('check_copyright', False),
            'check_ethical': data.get('check_ethical', False),
            'check_consent': data.get('check_consent', False),
            'check_acknowledgements': data.get('check_acknowledgements', False),
            'is_used_previous': data.get('is_used_previous', False),
            'word_count': data.get('word_count'),
            'is_corresponding_author': data.get('is_corresponding_author', False),
            'main_author_id': data.get('main_author_id'),
            'sub_author_ids': data.get('sub_author_ids', []),
            'is_competing_interests': data.get('is_competing_interests', False),
            'notes': data.get('notes'),
            'file_authors': data.get('file_authors'),
            'file_anonymized': data.get('file_anonymized'),
            'updated_at': int(time.time())
        }

        if submission_id:
            submission = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
            if not submission:
                return jsonify({'success': False, 'message': 'Submission not found'})

            dbc.submissions.get(id=submission_id).update(**submission_data).exec()
            return jsonify({'success': True, 'message': 'Article submitted successfully'})

        submission_data['created_date'] = int(time.time())
        result = dbc.submissions.add(**submission_data).exec()
        if result:
            return jsonify({'success': True, 'message': 'Article submitted successfully', 'submission_id': result[0]['id']})

        return jsonify({'success': False, 'message': 'Failed to submit article'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error submitting article: {str(e)}'})


def app__api_article_upload():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['file']
    file_type = request.form.get('file_type', 'authors')

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file and allowed_file(file.filename, {'pdf', 'doc', 'docx'}):
        filename = secure_filename(file.filename)
        filename = f"{file_type}_{user_id}_{int(time.time())}_{filename}"
        filepath = os.path.join(settings.SAVE_PATH, 'static', 'uploads', 'articles', filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)

        return jsonify({'success': True, 'file_path': f"/static/uploads/articles/{filename}"})

    return jsonify({'success': False, 'message': 'Invalid file type'})


def app__api_article_load(submission_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    submission = dbc.submissions.get(id=submission_id, user_id=user_id).exec()
    if not submission:
        return jsonify({'success': False, 'message': 'Submission not found'})

    submission = submission[0]
    return jsonify({'success': True, 'submission': submission})


def app__api_payment_submit_proof():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    if 'payment_proof' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['payment_proof']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file and allowed_file(file.filename, {'pdf', 'jpg', 'jpeg', 'png'}):
        filename = secure_filename(file.filename)
        filename = f"payment_proof_{user_id}_{int(time.time())}.{filename.rsplit('.', 1)[1].lower()}"

        payments_folder = os.path.join(settings.SAVE_PATH, 'static', 'uploads', 'payments')
        os.makedirs(payments_folder, exist_ok=True)
        filepath = os.path.join(payments_folder, filename)
        file.save(filepath)

        payment_data = {
            'user_id': user_id,
            'status': 'pending',
            'currency': request.form.get('currency', 'usd'),
            'payment_type': request.form.get('payment_type'),
            'payment_date': int(time.time()),
            'amount': float(request.form.get('amount', 0)),
            'ids': request.form.getlist('ids[]'),
            'proof': f"/static/uploads/payments/{filename}",
            'note': request.form.get('note'),
            'created_at': int(time.time())
        }

        dbc.payments.add(**payment_data).exec()
        return jsonify({'success': True, 'message': 'Payment proof submitted successfully'})

    return jsonify({'success': False, 'message': 'Invalid file type'})


def app__api_payment_delete(payment_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    payment = dbc.payments.get(id=payment_id, user_id=user_id).exec()
    if not payment:
        return jsonify({'success': False, 'message': 'Payment not found'})

    dbc.payments.get(id=payment_id, user_id=user_id).delete().exec()
    return jsonify({'success': True, 'message': 'Payment deleted successfully'})


def app__api_payment_create_subscription():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json() if request.is_json else request.form
    tariff_id = data.get('tariff_id')
    if not tariff_id:
        return jsonify({'success': False, 'message': 'Tariff ID required'})

    tariff = dbc.tariffs.get(id=int(tariff_id)).exec()
    if not tariff:
        return jsonify({'success': False, 'message': 'Tariff not found'})

    tariff = tariff[0]
    payment_data = {
        'user_id': user_id,
        'status': 'pending',
        'currency': data.get('currency', 'usd'),
        'payment_type': 'subscription',
        'payment_date': int(time.time()),
        'amount': float(data.get('amount', 0)),
        'ids': [int(tariff_id)],
        'proof': None,
        'note': data.get('note'),
        'created_at': int(time.time())
    }

    dbc.payments.add(**payment_data).exec()
    return jsonify({'success': True, 'message': 'Subscription payment created'})


def app__api_issue_purchase():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json() if request.is_json else request.form
    issue_id = data.get('issue_id')
    if not issue_id:
        return jsonify({'success': False, 'message': 'Issue ID required'})

    issue = dbc.issues.get(id=int(issue_id)).exec()
    if not issue:
        return jsonify({'success': False, 'message': 'Issue not found'})

    issue = issue[0]
    payment_data = {
        'user_id': user_id,
        'status': 'pending',
        'currency': data.get('currency', 'usd'),
        'payment_type': 'issue',
        'payment_date': int(time.time()),
        'amount': float(data.get('amount', 0)),
        'ids': [int(issue_id)],
        'proof': None,
        'note': data.get('note'),
        'created_at': int(time.time())
    }

    dbc.payments.add(**payment_data).exec()
    return jsonify({'success': True, 'message': 'Issue payment created'})


def app__api_translations_clear_cache():
    clear_translations_cache()
    return jsonify({'success': True, 'message': 'Translation cache cleared'})


def app__api_profile_change_password():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User not logged in'})

    data = request.get_json() if request.is_json else request.form
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    if not all([current_password, new_password, confirm_password]):
        return jsonify({'success': False, 'message': 'All fields are required'})

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})

    user = dbc.users.get(id=user_id).exec()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})

    user = user[0]
    if not check_password_hash(user['password'], current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})

    hashed_password = generate_password_hash(new_password)
    dbc.users.get(id=user_id).update(password=hashed_password).exec()
    return jsonify({'success': True, 'message': 'Password updated successfully'})


def app__api_createauthor():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Invalid request format - JSON expected'})

    data = request.get_json()
    orcid = data.get('orcid')
    name = data.get('name')
    without_orcid = data.get('without_orcid', False)

    if not name:
        return jsonify({'success': False, 'message': 'Required field missing: name'})

    if not name.strip() or len(name.strip()) < 2:
        return jsonify({'success': False, 'message': 'Author name must be at least 2 characters long'})

    if without_orcid:
        orcid = 'without-orcid'
    else:
        if not orcid:
            return jsonify({'success': False, 'message': 'Required field missing: ORCID (or check "Author without ORCID")'})
        if not orcid.strip() or len(orcid.strip()) < 10:
            return jsonify({'success': False, 'message': 'Invalid ORCID format. Please enter a valid ORCID (e.g., 0000-0000-0000-0000)'})

    try:
        if orcid != 'without-orcid':
            existing_author = dbc.author_profile.get(orcid=orcid.strip()).exec()
            if existing_author:
                return jsonify({'success': False, 'message': f'Author with ORCID {orcid} already exists in the database'})

        profile_data = {
            'user_id': None,
            'name': name.strip(),
            'organization': data.get('organization', '').strip(),
            'department': data.get('department', '').strip(),
            'position': data.get('position', '').strip(),
            'email': data.get('email', '').strip(),
            'phone': data.get('phone', '').strip(),
            'orcid': orcid.strip(),
            'address_street': data.get('address_street', '').strip(),
            'address_city': data.get('address_city', '').strip(),
            'address_country': data.get('address_country', '').strip(),
            'address_zip': data.get('address_zip', '').strip(),
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }

        result = dbc.author_profile.add(**profile_data).exec()
        if result:
            new_author = result[0]
            return jsonify({
                'success': True,
                'message': f'Author "{name}" created successfully',
                'author': {
                    'id': new_author['id'],
                    'name': new_author['name'],
                    'orcid': new_author['orcid'],
                    'organization': new_author['organization'],
                    'department': new_author['department'],
                    'position': new_author['position'],
                    'email': new_author['email'],
                    'phone': new_author['phone'],
                    'address_street': new_author['address_street'],
                    'address_city': new_author['address_city'],
                    'address_country': new_author['address_country'],
                    'address_zip': new_author['address_zip']
                }
            })
        return jsonify({'success': False, 'message': 'Failed to create author: Database operation returned no results'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error occurred while creating author: {str(e)}'})


def register(app):
    app.add_url_rule('/api/getauthor', view_func=login_required(app__api_getauthor), methods=['POST'])
    app.add_url_rule('/api/getcurrentauthor', view_func=login_required(app__api_getcurrentauthor), methods=['GET'])
    app.add_url_rule('/api/getclassifications', view_func=login_required(app__api_getclassifications), methods=['GET'])
    app.add_url_rule('/api/article/save', view_func=login_required(app__api_article_save), methods=['POST'])
    app.add_url_rule('/api/article/submit', view_func=login_required(app__api_article_submit), methods=['POST'])
    app.add_url_rule('/api/article/upload', view_func=login_required(app__api_article_upload), methods=['POST'])
    app.add_url_rule('/api/article/load/<int:submission_id>', view_func=login_required(app__api_article_load))
    app.add_url_rule('/api/payment/submit_proof', view_func=login_required(app__api_payment_submit_proof), methods=['POST'])
    app.add_url_rule('/api/payment/delete/<int:payment_id>', view_func=login_required(app__api_payment_delete), methods=['POST'])
    app.add_url_rule('/api/payment/create_subscription', view_func=login_required(app__api_payment_create_subscription), methods=['POST'])
    app.add_url_rule('/api/issue/purchase', view_func=login_required(app__api_issue_purchase), methods=['POST'])
    app.add_url_rule('/api/translations/clear_cache', view_func=login_required(app__api_translations_clear_cache), methods=['POST'])
    app.add_url_rule('/api/profile/change_password', view_func=login_required(app__api_profile_change_password), methods=['POST'])
    app.add_url_rule('/api/createauthor', view_func=login_required(app__api_createauthor), methods=['POST'])
