"""
BCMS – Beauty Center Management System
إعدادات المشروع — secrets loaded from secrets.json
"""
import json
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
SECRETS_FILE = BASE_DIR / 'secrets.json'


def load_secrets():
    try:
        with SECRETS_FILE.open(encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise ImproperlyConfigured("Create secrets.json in project root") from exc


creds = load_secrets()


def get_secret(key, default=None):
    if key in creds:
        return creds[key]
    if default is not None:
        return default
    raise ImproperlyConfigured(f'Missing "{key}" in secrets.json')


SECRET_KEY = get_secret('SECRET_KEY')
DEBUG = get_secret('DEBUG', False)
ALLOWED_HOSTS = get_secret('ALLOWED_HOSTS', ['localhost', '127.0.0.1'])


def _build_default_csrf_trusted_origins(hosts):
    origins = []
    for host in hosts:
        host = str(host).strip()
        if not host or host == '*':
            continue
        if '://' in host:
            origins.append(host)
            continue
        if host.startswith('.'):
            host = f'*.{host[1:]}'
        origins.append(f'https://{host}')
        origins.append(f'http://{host}')
    return list(dict.fromkeys(origins))


CSRF_TRUSTED_ORIGINS = get_secret(
    'CSRF_TRUSTED_ORIGINS',
    _build_default_csrf_trusted_origins(ALLOWED_HOSTS),
)

if get_secret('USE_REVERSE_PROXY_SSL_HEADER', False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'corsheaders',
    'whitenoise.runserver_nostatic',

    'apps.core',
    'apps.accounts',
    'apps.services',
    'apps.clients',
    'apps.staff',
    'apps.appointments',
    'apps.billing',
    'apps.finance',
    'apps.products',
    'apps.store',
    'apps.reports',
    'apps.sysadmin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'apps.core.middleware.NoCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.CenterMiddleware',
]

ROOT_URLCONF = 'PROJECT.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.center_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'PROJECT.wsgi.application'
ASGI_APPLICATION = 'PROJECT.asgi.application'

# ── Database ────────────────────────────────────────────────────
_db = get_secret('DATABASE')
if _db.get('ENGINE') == 'django.db.backends.sqlite3':
    # SQLite: resolve NAME relative to BASE_DIR
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / _db.get('NAME', 'db.sqlite3'),
        }
    }
else:
    DATABASES = {'default': _db}

# ── Auth ────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['apps.accounts.backends.UsernameBackend']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 6}},
]

# ── Localisation ─────────────────────────────────────────────────
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Khartoum'
USE_I18N = True
USE_L10N = False
USE_TZ = True

# ── Static / Media ───────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Session / Login ──────────────────────────────────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
SESSION_COOKIE_AGE = 86400 * 30
SESSION_COOKIE_NAME = 'bcms_session'
SESSION_SAVE_EVERY_REQUEST = True

# ── Email ────────────────────────────────────────────────────────
_email_cfg    = get_secret('EMAIL', {})
_email_noreply = _email_cfg.get('NOREPLY', {})

EMAIL_BACKEND       = _email_cfg.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = _email_noreply.get('HOST', '')
EMAIL_PORT          = int(_email_noreply.get('PORT', 587))
EMAIL_HOST_USER     = _email_noreply.get('USER', '')
EMAIL_HOST_PASSWORD = _email_noreply.get('PASSWORD', '')
EMAIL_USE_SSL       = str(_email_cfg.get('EMAIL_USE_SSL', 'False')).lower() == 'true'
EMAIL_USE_TLS       = not EMAIL_USE_SSL
DEFAULT_FROM_EMAIL  = f'BCMS <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else 'BCMS <noreply@bcms.app>'
