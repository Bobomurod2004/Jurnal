# flake8: noqa
import os
import time
from flask import render_template, session, request, jsonify, flash, redirect, url_for, current_app
from extensions import dbc
from modules.translate import t, translate
from utils.auth import login_required, sanitize_input
from utils.uploads import allowed_file


def app__dashboard():
    submissions = dbc.submissions.get().equal(user_id=session['user_id']).unequal(status='draft').order_by('id').per_page(5).page(1).exec()
    for submission in submissions:
        submission = translate(submission)
    return render_template('dashboard/index.html', submissions=submissions)


def app__dashboard_articles():
    submissions = dbc.submissions.get().equal(user_id=session['user_id']).unequal(status='draft').order_by('id').exec()
    author_profiles = {}

    # Collect unique author IDs first to avoid repeated DB lookups in template rendering.
    author_ids = set()
    for submission in submissions:
        translate(submission)
        if submission.get('main_author_id'):
            author_ids.add(submission['main_author_id'])

        co_author_ids = submission.get('sub_author_ids') or submission.get('subauthor_ids') or []
        for author_id in co_author_ids:
            author_ids.add(author_id)

    for author_id in author_ids:
        author = dbc.author_profile.get(id=author_id).exec()
        if author:
            author_profiles[author_id] = translate(author[0])

    return render_template('dashboard/articles.html', submissions=submissions, author_profiles=author_profiles)


def app__dashboard_articles_delete(submission_id):
    expects_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json
    submission = dbc.submissions.get(id=submission_id, user_id=session['user_id']).exec()
    if not submission:
        if expects_json:
            return jsonify({'success': False, 'message': t('submission_not_found')}), 404
        flash('Submission not found', 'error')
        return redirect(url_for('app__dashboard_articles'))

    dbc.submissions.get(id=submission_id, user_id=session['user_id']).delete().exec()
    if expects_json:
        return jsonify({'success': True, 'message': t('submission_deleted_successfully')})
    flash('Submission deleted successfully', 'success')
    return redirect(url_for('app__dashboard_articles'))


def app__dashboard_purchases():
    payments = dbc.payments.get(user_id=session['user_id']).unequal(status='unpaid').order_by('id').exec()
    for payment in payments:
        payment = translate(payment)
        if payment['payment_type'] == 'article' and payment['ids']:
            articles = []
            for article_id in payment['ids']:
                publication = dbc.publications.get(id=article_id).exec()
                if publication:
                    translated_article = translate(publication[0])
                    main_author = None
                    if translated_article['main_author_id']:
                        author = dbc.author_profile.get(id=translated_article['main_author_id']).exec()
                        if author:
                            main_author = translate(author[0])
                    articles.append({
                        'id': translated_article['id'],
                        'title': translated_article['title'],
                        'author': main_author['name'] if main_author else 'Unknown',
                        'volume': translated_article.get('volume', 'N/A'),
                        'issue': translated_article.get('issue', 'N/A'),
                        'year': time.strftime('%Y', time.gmtime(translated_article['created_date'] + 5 * 60 * 60))
                    })
            payment['articles'] = articles
        elif payment['payment_type'] == 'subscription' and payment['ids']:
            tariff_id = payment['ids'][0]
            tariff = dbc.tariffs.get(id=tariff_id).exec()
            if tariff:
                tariff_data = translate(tariff[0])
                payment['tariff'] = tariff_data

    subscription_active = False
    subscription_end_date = None
    days_left = None
    user = dbc.users.get(id=session['user_id']).exec()[0]
    if user.get('subscription_end_date') and user['subscription_end_date'] > int(time.time()):
        subscription_active = True
        subscription_end_date = time.strftime('%d.%m.%Y', time.gmtime(user['subscription_end_date']))
        days_left = (user['subscription_end_date'] - int(time.time())) // (24 * 60 * 60)

    tariffs = dbc.tariffs.get().exec()
    processed_tariffs = []
    for tariff in tariffs:
        tariff = translate(tariff)
        processed_tariffs.append(tariff)

    currency = request.args.get('currency', 'usd')
    is_verified = False
    if user.get('is_verified'):
        is_verified = True

    return render_template(
        'dashboard/payments.html',
        payments=payments,
        subscription_active=subscription_active,
        subscription_end_date=subscription_end_date,
        days_left=days_left,
        tariffs=processed_tariffs,
        currency=currency,
        is_verified=is_verified
    )


def app__dashboard_new_article():
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

    return render_template('dashboard/new_article.html',
                         translations=translations,
                         authors=authors,
                         classifications=classifications,
                         countries=countries)


def app__dashboard_payments():
    return app__dashboard_purchases()


def app__dashboard_guides():
    return render_template('dashboard/guides.html')


def app__dashboard_profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_photo':
            if 'photo' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})

            file = request.files['photo']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})

            if file and allowed_file(file.filename):
                filename = f"avatar_{session['user_id']}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}"
                filepath = os.path.join(current_app.config['AVATARS_FOLDER'], filename)

                user = dbc.users.get(id=session['user_id']).exec()[0]
                if user['avatar']:
                    try:
                        old_avatar_path = os.path.join('static', user['avatar'].lstrip('/'))
                        if os.path.exists(old_avatar_path):
                            os.remove(old_avatar_path)
                    except (FileNotFoundError, OSError):
                        pass

                file.save(filepath)

                dbc.users.get(id=session['user_id']).update(
                    avatar=f"/static/uploads/avatars/{filename}"
                ).exec()

                return jsonify({'success': True})

            return jsonify({'success': False, 'message': 'Invalid file type'})

        if action == 'delete_photo':
            user = dbc.users.get(id=session['user_id']).exec()[0]
            if user['avatar']:
                try:
                    os.remove(os.path.join('static', user['avatar'].lstrip('/')))
                except (FileNotFoundError, OSError):
                    pass

                dbc.users.get(id=session['user_id']).update(
                    avatar=None
                ).exec()

            return jsonify({'success': True})

        if action == 'save_profile':
            country_id = request.form.get('country_id')
            if country_id:
                country = dbc.fix_country.get(id=country_id).exec()
                if not country:
                    flash('Invalid country selected', 'error')
                    return redirect(url_for('app__dashboard_profile'))

            user = dbc.users.get(id=session['user_id']).exec()[0]
            existing_doc_upload = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()

            orcid = request.form.get('orcid')
            if orcid:
                orcid = sanitize_input(orcid)

            profile_data = {
                'name': sanitize_input(request.form.get('name')),
                'organization': sanitize_input(request.form.get('organization')),
                'department': sanitize_input(request.form.get('department')),
                'position': sanitize_input(request.form.get('position')),
                'email': sanitize_input(request.form.get('email')),
                'phone': sanitize_input(request.form.get('phone')),
                'orcid': orcid,
                'address_street': sanitize_input(request.form.get('address_street')),
                'address_city': sanitize_input(request.form.get('address_city')),
                'address_country': sanitize_input(request.form.get('address_country')),
                'address_zip': sanitize_input(request.form.get('address_zip')),
                'updated_at': int(time.time())
            }

            author_profile = dbc.author_profile.get(user_id=session['user_id']).exec()
            if author_profile:
                dbc.author_profile.get(user_id=session['user_id']).update(**profile_data).exec()
            else:
                profile_data['created_at'] = int(time.time())
                dbc.author_profile.add(**profile_data).exec()

            flash('Author profile updated successfully', 'success')
            return redirect(url_for('app__dashboard_profile'))

        if action == 'upload_academic_document':
            if 'academic_document' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})

            file = request.files['academic_document']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})

            if file and allowed_file(file.filename, {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}):
                timestamp = int(time.time())
                filename = f"academic_doc_{session['user_id']}_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}"

                existing_doc_upload = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()
                documents_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
                os.makedirs(documents_folder, exist_ok=True)

                filepath = os.path.join(documents_folder, filename)

                if existing_doc_upload and existing_doc_upload[0].get('file_path'):
                    try:
                        old_doc_path = os.path.join('static', existing_doc_upload[0]['file_path'].lstrip('/'))
                        if os.path.exists(old_doc_path):
                            os.remove(old_doc_path)
                    except (FileNotFoundError, OSError):
                        pass

                file.save(filepath)

                return jsonify({
                    'success': True,
                    'file_path': f"/static/uploads/documents/{filename}",
                    'filename': filename
                })

            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PDF, DOC, DOCX, JPG, PNG'})

    user = dbc.users.get(id=session['user_id']).exec()[0]
    author_profile = dbc.author_profile.get(user_id=session['user_id']).exec()
    user_doc_upload = dbc.user_doc_uploads.get(user_id=session['user_id']).exec()
    fix_country = dbc.fix_country.get().exec()

    return render_template('dashboard/profile.html',
                         user=user,
                         author_profile=author_profile[0] if author_profile else None,
                         user_doc_upload=user_doc_upload[0] if user_doc_upload else None,
                         fix_country=fix_country)


def register(app):
    app.add_url_rule('/dashboard', view_func=login_required(app__dashboard))
    app.add_url_rule('/dashboard/articles', view_func=login_required(app__dashboard_articles))
    app.add_url_rule('/dashboard/articles/delete/<int:submission_id>', view_func=login_required(app__dashboard_articles_delete), methods=['POST'])
    app.add_url_rule('/dashboard/purchases', view_func=login_required(app__dashboard_purchases))
    app.add_url_rule('/dashboard/new_article', view_func=login_required(app__dashboard_new_article))
    app.add_url_rule('/dashboard/payments', view_func=login_required(app__dashboard_payments))
    app.add_url_rule('/dashboard/guides', view_func=login_required(app__dashboard_guides))
    app.add_url_rule('/dashboard/profile', view_func=login_required(app__dashboard_profile), methods=['GET', 'POST'])
