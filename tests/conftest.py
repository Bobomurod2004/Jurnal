import os
import sys
import types
import importlib

# Disable DB init for unit tests.
os.environ.setdefault('SKIP_DB_INIT', '1')
os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('APP_VERSION', 'test')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MAINWEB_DIR = os.path.join(ROOT_DIR, 'mainweb')
FMADMIN_DIR = os.path.join(ROOT_DIR, 'fmadmin')

for path in (ROOT_DIR, MAINWEB_DIR, FMADMIN_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)


def _merge_modules(module_name, source_module_names):
    merged = types.ModuleType(module_name)
    for source_name in source_module_names:
        source_module = importlib.import_module(source_name)
        for attr_name in dir(source_module):
            if attr_name.startswith('__'):
                continue
            if not hasattr(merged, attr_name):
                setattr(merged, attr_name, getattr(source_module, attr_name))
    return merged


def _install_import_aliases():
    fm_extensions = importlib.import_module('fmadmin.extensions')
    mw_extensions = importlib.import_module('mainweb.extensions')

    extensions_module = types.ModuleType('extensions')
    extensions_module.db = getattr(fm_extensions, 'db', None)
    extensions_module.dbc = getattr(mw_extensions, 'dbc', None)
    sys.modules['extensions'] = extensions_module

    translate_module = importlib.import_module('mainweb.modules.translate')
    modules_package = types.ModuleType('modules')
    modules_package.translate = translate_module
    sys.modules['modules'] = modules_package
    sys.modules['modules.translate'] = translate_module

    utils_package = types.ModuleType('utils')
    utils_package.__path__ = []
    sys.modules['utils'] = utils_package

    merged_roles = _merge_modules('utils.roles', ('mainweb.utils.roles', 'fmadmin.utils.roles'))
    sys.modules['utils.roles'] = merged_roles
    setattr(utils_package, 'roles', merged_roles)

    merged_notifications = _merge_modules('utils.notifications', ('mainweb.utils.notifications', 'fmadmin.utils.notifications'))
    merged_private_uploads = _merge_modules('utils.private_uploads', ('mainweb.utils.private_uploads', 'fmadmin.utils.private_uploads'))
    uploads_module = importlib.import_module('mainweb.utils.uploads')
    emailer_module = importlib.import_module('mainweb.utils.emailer')
    # fmadmin first: it owns the admin-timezone helpers that fmadmin routes
    # import, and mainweb fills in the rest (richtext, covers, currency).
    merged_filters = _merge_modules('utils.filters', ('fmadmin.utils.filters', 'mainweb.utils.filters'))
    module_map = {
        'notifications': merged_notifications,
        'private_uploads': merged_private_uploads,
        'uploads': uploads_module,
        'emailer': emailer_module,
        'filters': merged_filters,
    }
    for short_name, module in module_map.items():
        full_name = f'utils.{short_name}'
        sys.modules[full_name] = module
        setattr(utils_package, short_name, module)

    merged_auth = _merge_modules('utils.auth', ('mainweb.utils.auth', 'fmadmin.utils.auth'))
    sys.modules['utils.auth'] = merged_auth
    setattr(utils_package, 'auth', merged_auth)


_install_import_aliases()
