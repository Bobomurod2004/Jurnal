import os
import settings

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def init_uploads(app):
    upload_folder = os.path.join(settings.SAVE_PATH, 'static', 'uploads')
    avatars_folder = os.path.join(upload_folder, 'avatars')
    articles_folder = os.path.join(upload_folder, 'articles')
    documents_folder = os.path.join(upload_folder, 'documents')

    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['AVATARS_FOLDER'] = avatars_folder
    app.config['ARTICLES_FOLDER'] = articles_folder
    app.config['DOCUMENTS_FOLDER'] = documents_folder

    os.makedirs(avatars_folder, exist_ok=True)
    os.makedirs(articles_folder, exist_ok=True)
    os.makedirs(documents_folder, exist_ok=True)


def allowed_file(filename, extensions=ALLOWED_EXTENSIONS):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions
