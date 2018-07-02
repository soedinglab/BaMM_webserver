"""
Django settings for webserver project.

Generated by 'django-admin startproject' using Django 1.8.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from os import path


class MissingConfigurationException(Exception):
    pass


def get_from_env(env_variable, converter=str):
    if env_variable not in os.environ:
        raise MissingConfigurationException('Environment variable %s undefined' % env_variable)
    else:
        return converter(os.getenv(env_variable))


N_PARALLEL_THREADS = get_from_env('N_CORES_PER_JOB', int)

# CELERY SETTINGS
BROKER_URL = 'redis://redis_celery:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = get_from_env('SECRET_KEY')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_from_env('DJANGO_DEBUG', converter=lambda x: x == "1")

ALLOWED_HOSTS = get_from_env('ALLOWED_HOSTS', converter=lambda x: x.split())
# Application definition

SESSION_COOKIE_AGE = 3600 * 24 * 7 * 4  # four weeks 
SESSION_SAVE_EVERY_REQUEST = True

INSTALLED_APPS = (
    'bammmotif',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'dbbackup',
    'widget_tweaks',
)


MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'webserver.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
#        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders' : [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader'
            ]
        },
    },
]

WSGI_APPLICATION = 'webserver.wsgi.application'

DB_ROOT = os.path.join(BASE_DIR, '/DB')


DB_HOST = get_from_env('DB_HOST')
DB_NAME = get_from_env('DB_NAME')
DB_USER = get_from_env('DB_USER')
DB_PORT = get_from_env('DB_PORT')
DB_PW = get_from_env('MYSQL_PASSWORD')

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PW,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}


# Restriction of data upload for registered and anonymous users.
# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
# 100MB 104857600
# 250MB - 214958080
# 500MB - 429916160
MAX_UPLOAD_SIZE = "429916160"
MAX_UPLOAD_SIZE_ANONYMOUS = "429916160"

# Redirect after successful authentication
LOGIN_REDIRECT_URL = 'home'
# Redirect after successful logout
LOGOUT_REDIRECT_URL = 'home'

# User Registrations specific settings
ACCOUNT_ACTIVATION_DAYS = 7


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# File Folder Redirection
# https://docs.djangoproject.com/en/1.10/ref/settings/#media-root

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles'),
    os.path.join(BASE_DIR, 'BaMM_webserver/DB')
]

# Settings related to file system structure
JOB_DIR_PREFIX = ''
JOB_DIR = path.join(MEDIA_ROOT, JOB_DIR_PREFIX)
MOTIF_DATABASE_PATH = '/motif_db'
STATICFILES_DIRS.append(MOTIF_DATABASE_PATH)
LOG_DIR = '/logs'

# Settings realted to example data
EXAMPLE_DIR = 'example_data'
EXAMPLE_FASTA = 'example_data/ExampleData.fasta'
EXAMPLE_MOTIF = 'example_data/ExampleMotifs.meme'
PENG_INIT = 'PengInitialization.meme'
PENG_OUT = 'PengOut.meme'
BAMM_INPUT = 'Input'

# email logging configuration
EMAIL_LOGGER_LEVEL = get_from_env('EMAIL_LOGGER_LEVEL')
EMAIL_LOGGER_SERVER = get_from_env('EMAIL_LOGGER_SERVER')
EMAIL_LOGGER_PORT = get_from_env('EMAIL_LOGGER_PORT', converter=int)
EMAIL_LOGGER_FROM = get_from_env('EMAIL_LOGGER_FROM')
EMAIL_LOGGER_TO = get_from_env('EMAIL_LOGGER_TO')
EMAIL_LOGGER_USER = get_from_env('EMAIL_LOGGER_USER')
EMAIL_LOGGER_PASSWORD = get_from_env('EMAIL_LOGGER_PASSWORD')
EMAIL_LOGGER_USE_TLS = get_from_env('EMAIL_LOGGER_USE_TLS', converter=lambda x: x == '1')
EMAIL_LOGGER_SUBJECT = get_from_env('EMAIL_LOGGER_SUBJECT')

USE_EMAIL_LOGGER = EMAIL_LOGGER_LEVEL != 'OFF'


# logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(module)s: %(message)s',
        },
    },
    'handlers': {
        'django_logfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024*1024*100,
            'backupCount': 5,
            'filename': path.join(LOG_DIR, 'django.log'),
            'formatter': 'verbose'
        },
        'django_requests_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024*1024*100,
            'backupCount': 5,
            'filename': path.join(LOG_DIR, 'django_requests.log'),
            'formatter': 'verbose'
        },
        'bammmotif_logfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024*1024*100,
            'backupCount': 5,
            'filename': path.join(LOG_DIR, 'bammmotif.log'),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['django_logfile'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['django_requests_file'],
            'level': 'WARN',
            'propagate': True,
        },
        'bammmotif': {
            'handlers': ['bammmotif_logfile'],
            'level': get_from_env('BAMM_LOG_LEVEL'),
            'propagate': True,
        }
    }
}

if USE_EMAIL_LOGGER:
    LOGGING['handlers']['bammmotif_email'] = {
        'class': 'bammmotif.logging.TlsSMTPHandler',
        'mailhost': (EMAIL_LOGGER_SERVER, EMAIL_LOGGER_PORT),
        'fromaddr': EMAIL_LOGGER_FROM,
        'toaddrs': [EMAIL_LOGGER_TO],
        'subject': EMAIL_LOGGER_SUBJECT,
        'credentials': (EMAIL_LOGGER_USER, EMAIL_LOGGER_PASSWORD),
        'level': EMAIL_LOGGER_LEVEL,
        'use_tls': EMAIL_LOGGER_USE_TLS,
    }
    LOGGING['loggers']['bammmotif']['handlers'].append('bammmotif_email')

# Miscellaneous configuration
MAX_FINDJOB_DAYS = get_from_env('MAX_FINDJOB_DAYS', converter=int)
MAX_UPLOAD_FILE_SIZE = get_from_env('MAX_UPLOAD_FILE_SIZE', converter=int)
MAX_SEEDS_FOR_REFINEMENT = get_from_env('MAX_SEEDS_FOR_REFINEMENT', converter=int)
DEFAULT_SEEDS_FOR_REFINEMENT = get_from_env('DEFAULT_SEEDS_FOR_REFINEMENT', converter=int)
DEFAULT_MOTIF_DB = get_from_env('DEFAULT_MOTIF_DB')
ZIP_INCLUDE_ZOOPS_STATS = get_from_env('ZIP_INCLUDE_ZOOPS_STATS', converter=lambda x: x == "1")
MIN_FASTA_SEQUENCES = get_from_env('MIN_FASTA_SEQUENCES', converter=int)
FDR_CV_FOLD = get_from_env('FDR_CV_FOLD', converter=int)

# cleanup settings
MAX_JOB_STORAGE_DAYS = get_from_env('MAX_JOB_STORAGE_DAYS', converter=int)
MAX_INPUT_STORAGE_DAYS = get_from_env('MAX_INPUT_STORAGE_DAYS', converter=int)
DAILY_CLEANUP_HOUR_UTC = get_from_env('DAILY_CLEANUP_HOUR_UTC', converter=int)


# backup settings
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': '/backup'}
DBBACKUP_CLEANUP_KEEP = get_from_env('N_STORED_BACKUPS', converter=int)
DBBACKUP_CLEANUP_KEEP_MEDIA = get_from_env('N_STORED_BACKUPS', converter=int)
DAILY_BACKUP_HOUR_UTC = get_from_env('DAILY_BACKUP_HOUR_UTC', converter=int)
