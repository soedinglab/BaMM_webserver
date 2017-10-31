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

# CELERY SETTINGS
BROKER_URL = 'redis://redis_celery:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3&umq7d9gtpb=8atu$z8+#n92f--yk%yv_=v%c05&*+pwod7l='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['0.0.0.0','bammmotif.mpibpc.mpg.de']


# Application definition

INSTALLED_APPS = (
    'bammmotif',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
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


DB_HOST = 'db'
DB_NAME = 'webserver'
DB_USER = 'root'
DB_PW = '3aMM!mot1f'
DB_PORT = '3306'

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
MAX_UPLOAD_SIZE_ANONYMOUS = "2621440"

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

TIME_ZONE = 'UTC'‚

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'staticfiles'),
    os.path.join(BASE_DIR, 'BaMM_webserver/DB')
)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email.gwdg.de'
EMAIL_HOST_PASSWORD = 'BaMM_motif11610'
EMAIL_HOST_USER = 'bamm@mpibpc.mpg.de'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
SERVER_EMAIL = 'bamm@mpibpc.mpg.de'
DEFAULT_FROM_EMAIL = 'bamm@mpibpc.mpg.de'

EMAIL_SUBJECT_SUCCESS = str("BaMM!motif: Your Job has finished!")
EMAIL_MESSAGE_SUCCESS = str("Dear User, \n your BaMM!motif Job has finished. You can view its results following this link: xcxdxx\n\n Greetings from the BaMM!team\n")


# Settings related to file system structure
JOB_DIR_PREFIX = 'jobs'

# Settings realted to example data
EXAMPLE_FASTA = 'example_data/ExampleData.fasta'
EXAMPLE_MOTIF = 'example_data/ExampleMotif.meme' 
