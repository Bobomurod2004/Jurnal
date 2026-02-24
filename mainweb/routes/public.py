# flake8: noqa
import os
import time
from flask import render_template, session, request, jsonify, flash, redirect, url_for, send_file, send_from_directory
from extensions import dbc
from modules.translate import t, translate, clear_translations_cache
import settings
from utils.auth import login_required


def app__index():
    if 'language' not in session:
        browser_lang = request.accept_languages.best_match(['uz', 'ru', 'en'])
        session['language'] = browser_lang or 'en'
        session.modified = True

    latest_publications = dbc.publications.get().order_by('date_publish').per_page(8).page(1).exec()
    downloaded_publications = dbc.publications.get().order_by('stat_alt').per_page(8).page(1).exec()
    popular_publications = dbc.publications.get().order_by('stat_views').per_page(8).page(1).exec()

    for publications in [latest_publications, downloaded_publications, popular_publications]:
        for pub in publications:
            pub = translate(pub)
            if pub['main_author_id']:
                author = dbc.author_profile.get(id=pub['main_author_id']).exec()
                if author:
                    pub['main_author'] = translate(author[0])
            if pub['issue_id']:
                issue = dbc.issues.get(id=pub['issue_id']).exec()
                if issue:
                    pub['issue'] = translate(issue[0])

    return render_template(
        'index.html',
        latest_publications=latest_publications,
        downloaded_publications=downloaded_publications,
        popular_publications=popular_publications
    )


def app__editorial():
    editors = dbc.editors.get().exec()
    for editor in editors:
        editor = translate(editor)
    return render_template('mainweb/editorial.html', editors=editors)


def app__page_alias(alias):
    page = dbc.pages.get(alias=alias).exec()
    if not page:
        flash('Page not found', 'error')
        return redirect(url_for('app__index'))
    page = translate(page[0])
    return render_template('mainweb/page.html', page=page)


def app__contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        if name and email and message:
            flash('Message sent successfully', 'success')
        else:
            flash('All fields are required', 'error')
        return redirect(url_for('app__contact'))
    return render_template('mainweb/contact.html')


def app__articles():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    search_query = request.args.get('search', '').strip()
    issue_filter = request.args.get('issue', '')
    volume_filter = request.args.get('volume', '')
    year_filter = request.args.get('year', '')
    access_filter = request.args.get('access', '')
    sort_by = request.args.get('sort', 'newest')

    query = dbc.publications.get()

    if issue_filter:
        query = query.where(issue_id=int(issue_filter))

    if year_filter:
        year_issues = dbc.issues.get(year=int(year_filter)).exec()
        if year_issues:
            issue_ids = [issue['id'] for issue in year_issues]
            query = query.any(issue_id=issue_ids)
        else:
            query = query.get(id=-1)

    if volume_filter:
        volume_issues = dbc.issues.get(vol_no=volume_filter).exec()
        if volume_issues:
            issue_ids = [issue['id'] for issue in volume_issues]
            query = query.any(issue_id=issue_ids)
        else:
            query = query.get(id=-1)

    if access_filter:
        if access_filter == 'open':
            query = query.where(is_paid=False)
        elif access_filter == 'paid':
            query = query.where(is_paid=True, subscription_enable=False)
        elif access_filter == 'subscription':
            query = query.where(subscription_enable=True)

    if sort_by == 'newest':
        query = query.order_by('date_publish')
    elif sort_by == 'oldest':
        query = query.order_by('date_publish')
    elif sort_by == 'title_az':
        query = query.order_by('title')
    elif sort_by == 'title_za':
        query = query.order_by('title')
    elif sort_by == 'most_viewed':
        query = query.order_by('stat_views')
    elif sort_by == 'most_cited':
        pass
    else:
        query = query.order_by('date_publish')

    publications = query.per_page(per_page).page(page).exec()

    author_name_cache = {}
    issue_cache = {}
    references_count_cache = {}
    citations_count_cache = {}

    def get_author_name(author_id):
        if not author_id:
            return None
        if author_id not in author_name_cache:
            author_row = dbc.author_profile.get(id=author_id).exec()
            author_name_cache[author_id] = author_row[0].get('name') if author_row else None
        return author_name_cache[author_id]

    def get_issue(issue_id):
        if not issue_id:
            return None
        if issue_id not in issue_cache:
            issue_row = dbc.issues.get(id=issue_id).exec()
            issue_cache[issue_id] = issue_row[0] if issue_row else None
        return issue_cache[issue_id]

    def get_references_count(publication_id):
        if publication_id not in references_count_cache:
            references_count_cache[publication_id] = len(dbc.publication_refs.get(publication_id=publication_id).exec())
        return references_count_cache[publication_id]

    def get_citations_count(publication_id):
        if publication_id not in citations_count_cache:
            citations_count_cache[publication_id] = len(dbc.publication_citations.get(publication_id=publication_id).exec())
        return citations_count_cache[publication_id]

    if sort_by == 'oldest':
        publications = list(reversed(publications))
    elif sort_by == 'title_az':
        publications = sorted(publications, key=lambda x: x.get('title', '').lower())

    if search_query:
        filtered_publications = []
        lowered_search = search_query.lower()
        for pub in publications:
            search_fields = [
                pub.get('title', '').lower(),
                pub.get('abstract', '').lower(),
                ' '.join(pub.get('keywords', [])).lower()
            ]
            author_names = []
            if pub['main_author_id']:
                main_author_name = get_author_name(pub['main_author_id'])
                if main_author_name:
                    author_names.append(main_author_name.lower())

            co_author_ids = pub.get('subauthor_ids') or pub.get('sub_author_ids') or []
            for author_id in co_author_ids:
                co_author_name = get_author_name(author_id)
                if co_author_name:
                    author_names.append(co_author_name.lower())

            search_fields.extend(author_names)
            if any(lowered_search in field for field in search_fields):
                filtered_publications.append(pub)
        publications = filtered_publications

    processed_publications = []
    for pub in publications:
        author_names = []
        if pub['main_author_id']:
            main_author_name = get_author_name(pub['main_author_id'])
            if main_author_name:
                author_names.append(main_author_name)

        co_author_ids = pub.get('subauthor_ids') or pub.get('sub_author_ids') or []
        for author_id in co_author_ids:
            co_author_name = get_author_name(author_id)
            if co_author_name:
                author_names.append(co_author_name)

        issue = get_issue(pub['issue_id']) if pub.get('issue_id') else None
        references_count = get_references_count(pub['id'])
        citations_count = get_citations_count(pub['id'])

        processed_publications.append({
            'id': pub['id'],
            'title': pub['title'],
            'abstract': pub['abstract'],
            'authors': ', '.join(author_names),
            'date_publish': pub['date_publish'],
            'stat_views': pub.get('stat_views', 0),
            'stat_crossref': pub.get('stat_crossref', 0),
            'references_count': references_count,
            'citations_count': citations_count,
            'doi': pub.get('doi'),
            'keywords': pub.get('keywords', []),
            'is_paid': pub.get('is_paid', False),
            'subscription_enable': pub.get('subscription_enable', False),
            'issue': issue
        })

    if sort_by == 'most_cited':
        processed_publications = sorted(processed_publications, key=lambda x: x['citations_count'], reverse=True)

    all_issues = dbc.issues.get().order_by('year').exec()
    all_volumes = sorted(list(set([issue['vol_no'] for issue in all_issues if issue['vol_no']])), reverse=True)
    all_years = sorted(list(set([issue['year'] for issue in all_issues if issue['year']])), reverse=True)

    return render_template('mainweb/articles.html',
                         publications=processed_publications,
                         all_issues=all_issues,
                         all_volumes=all_volumes,
                         all_years=all_years,
                         current_filters={
                             'search': search_query,
                             'issue': issue_filter,
                             'volume': volume_filter,
                             'year': year_filter,
                             'access': access_filter,
                             'sort': sort_by
                         },
                         total_results=len(processed_publications),
                         page=page,
                         per_page=per_page)


def app__news():
    page = request.args.get('page', 1, type=int)
    per_page = 12

    all_items = dbc.news.get(status='published').order_by('published_at').per_page(per_page).page(page).exec()
    news_items = dbc.news.get(type='news', status='published').order_by('published_at').exec()
    announcements = dbc.news.get(type='announcement', status='published').order_by('published_at').exec()

    for item in all_items + news_items + announcements:
        item = translate(item)

    return render_template('mainweb/news.html',
                         all_items=all_items,
                         news_items=news_items,
                         announcements=announcements)


def app__news_detail(news_id):
    news_item = dbc.news.get(id=news_id, status='published').exec()
    if not news_item:
        flash('News item not found', 'error')
        return redirect(url_for('app__news'))

    news_item = translate(news_item[0])

    author = None
    if news_item.get('author_id'):
        author_data = dbc.author_profile.get(id=news_item['author_id']).exec()
        if author_data:
            author = author_data[0]

    related_items = dbc.news.get(type=news_item['type'], status='published').unequal(id=news_id).order_by('published_at').per_page(3).page(1).exec()
    for item in related_items:
        item = translate(item)

    return render_template('mainweb/news_detail.html',
                         news_item=news_item,
                         author=author,
                         related_items=related_items)


def app__change_language(lang):
    if lang in ['en', 'uz', 'ru']:
        session['language'] = lang
        session.modified = True
        clear_translations_cache()
        flash(f'language_changed_to_{lang}', 'success')
    else:
        flash('invalid_language', 'error')

    redirect_url = request.referrer
    if not redirect_url or 'change_language' in redirect_url:
        redirect_url = url_for('app__index')

    return redirect(redirect_url)


def app__issues():
    year_filter = request.args.get('year')
    category_filter = request.args.get('category')
    access_filter = request.args.get('access')

    query = dbc.issues.get()

    if year_filter:
        query = query.equal(year=int(year_filter))

    if category_filter:
        query = query.equal(category=category_filter)

    if access_filter:
        if access_filter == 'free':
            query = query.equal(is_paid=False)
        elif access_filter == 'paid':
            query = query.equal(is_paid=True)
        elif access_filter == 'subscription':
            query = query.equal(subscription_enable=True)

    issues = query.order_by('year').exec()
    issues = sorted(issues, key=lambda x: (x['year'], x['issue_no']), reverse=True)

    all_issues = dbc.issues.get().exec()
    available_years = sorted(set(issue['year'] for issue in all_issues), reverse=True)
    available_categories = dbc.fix_issue_categories.get().exec()
    for cat in available_categories:
        cat = translate(cat)
    return render_template('mainweb/issues.html',
                         issues=issues,
                         available_years=available_years,
                         available_categories=available_categories,
                         current_filters={
                             'year': year_filter,
                             'category': category_filter,
                             'access': access_filter
                         })


def app__issue(issue_id):
    issue = dbc.issues.get(id=issue_id).exec()
    if not issue:
        flash('Issue not found', 'error')
        return redirect(url_for('app__issues'))

    issue = issue[0]

    all_issues = dbc.issues.get().exec()
    all_issues = sorted(all_issues, key=lambda x: (x['year'], x['issue_no']))

    current_index = None
    for i, curr_issue in enumerate(all_issues):
        if curr_issue['id'] == issue_id:
            current_index = i
            break

    prev_issue = all_issues[current_index - 1] if current_index > 0 else None
    next_issue = all_issues[current_index + 1] if current_index < len(all_issues) - 1 else None

    has_access = False
    if 'user_id' in session:
        user = dbc.users.get(id=session['user_id']).exec()[0]
        if user.get('subscription_end_date') and user['subscription_end_date'] > int(time.time()):
            has_access = True
        else:
            payments = dbc.payments.get(user_id=session['user_id'], status='paid').exec()
            for payment in payments:
                if payment['payment_type'] == 'issue' and payment['ids'] and issue_id in payment['ids']:
                    has_access = True
                    break

    publications = dbc.publications.get(issue_id=issue_id).exec()
    articles = []

    if publications:
        for pub in publications:
            main_author = None
            if pub['main_author_id']:
                main_authors = dbc.author_profile.get(id=pub['main_author_id']).exec()
                if main_authors:
                    main_author = main_authors[0]

            co_authors = []
            if pub['subauthor_ids']:
                for author_id in pub['subauthor_ids']:
                    co_authors_result = dbc.author_profile.get(id=author_id).exec()
                    if co_authors_result:
                        co_authors.append(co_authors_result[0])

            authors = main_author['name'] if main_author else ''
            if co_authors:
                if authors:
                    authors += ', '
                authors += ', '.join(author['name'] for author in co_authors)

            articles.append({
                'id': pub['id'],
                'title': pub['title'],
                'authors': authors
            })
    issue = translate(issue)
    return render_template('mainweb/issue.html',
                         issue=issue,
                         has_access=has_access,
                         prev_issue=prev_issue,
                         next_issue=next_issue,
                         articles=articles)


def app__purchase_issue(issue_id):
    return redirect(url_for('app__issues'))


def app__article(article_id):
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = translate(publication[0])

    main_author = None
    if publication['main_author_id']:
        main_author = dbc.author_profile.get(id=publication['main_author_id']).exec()
        if main_author:
            main_author = translate(main_author[0])

    co_authors = []
    if publication['subauthor_ids']:
        for author_id in publication['subauthor_ids']:
            co_author = dbc.author_profile.get(id=author_id).exec()
            if co_author:
                co_authors.append(translate(co_author[0]))

    issue = None
    if publication['issue_id']:
        issue_data = dbc.issues.get(id=publication['issue_id']).exec()
        if issue_data:
            issue = translate(issue_data[0])

    parts = dbc.publication_parts.get(publication_id=article_id).order_by('order_id').exec()
    figures = dbc.publication_figures.get(publication_id=article_id).order_by('order_id').exec()

    references = dbc.publication_refs.get(publication_id=article_id).exec()
    citations = dbc.publication_citations.get(publication_id=article_id).exec()

    for ref in references:
        ref = translate(ref)
    for citation in citations:
        citation = translate(citation)

    return render_template('mainweb/article.html',
                         publication=publication,
                         main_author=main_author,
                         co_authors=co_authors,
                         issue=issue,
                         parts=parts,
                         figures=figures,
                         references=references,
                         citations=citations)


def app__download_article(article_id):
    publication = dbc.publications.get(id=article_id).exec()
    if not publication:
        flash('Article not found', 'error')
        return redirect(url_for('app__articles'))

    publication = publication[0]

    if publication['is_paid']:
        if 'user_id' not in session:
            flash('Please log in to download this article', 'error')
            return redirect(url_for('app__login'))

        user = dbc.users.get(id=session['user_id']).exec()[0]
        has_access = False
        if user.get('subscription_end_date') and user['subscription_end_date'] > int(time.time()):
            has_access = True
        else:
            payments = dbc.payments.get(user_id=session['user_id'], status='paid').exec()
            for payment in payments:
                if payment['payment_type'] == 'article' and payment['ids'] and article_id in payment['ids']:
                    has_access = True
                    break

        if not has_access:
            flash('Access denied. Please purchase or subscribe.', 'error')
            return redirect(url_for('app__article', article_id=article_id))

    if not publication.get('file_ids'):
        flash('Article file not found', 'error')
        return redirect(url_for('app__article', article_id=article_id))

    file_id = publication['file_ids'][0]
    file_record = dbc.files.get(id=file_id).exec()
    if not file_record:
        flash('Article file not found', 'error')
        return redirect(url_for('app__article', article_id=article_id))

    file_record = file_record[0]
    file_path = os.path.join(settings.SAVE_PATH, file_record['filepath'].lstrip('/'))

    if not os.path.exists(file_path):
        flash('Article file not found', 'error')
        return redirect(url_for('app__article', article_id=article_id))

    return send_file(file_path,
                    as_attachment=True,
                    download_name=f"{publication['title']}.pdf")


def serve_static_uploads(filename):
    return send_from_directory(os.path.join(settings.SAVE_PATH, 'static', 'uploads'), filename)


def register(app):
    app.add_url_rule('/', view_func=app__index)
    app.add_url_rule('/editorial', view_func=app__editorial)
    app.add_url_rule('/page/<string:alias>', view_func=app__page_alias)
    app.add_url_rule('/contact', view_func=app__contact, methods=['GET', 'POST'])
    app.add_url_rule('/articles', view_func=app__articles)
    app.add_url_rule('/news', view_func=app__news)
    app.add_url_rule('/news/<int:news_id>', view_func=app__news_detail)
    app.add_url_rule('/change_language/<string:lang>', view_func=app__change_language)
    app.add_url_rule('/issues', view_func=app__issues)
    app.add_url_rule('/issue/<int:issue_id>', view_func=app__issue)
    app.add_url_rule('/issue/purchase/<int:issue_id>', view_func=login_required(app__purchase_issue))
    app.add_url_rule('/article/<int:article_id>', view_func=app__article)
    app.add_url_rule('/article/download/<int:article_id>', view_func=app__download_article)
    app.add_url_rule('/static/uploads/<path:filename>', view_func=serve_static_uploads)
