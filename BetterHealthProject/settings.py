"""
Django settings for BetterHealthProject project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Import dj-database-url at the beginning of the file.
import dj_database_url
import os
import environ

# ── Rutas base ──
BASE_DIR = Path(__file__).resolve().parent.parent

# ── django-environ ───
env = environ.Env(
    # valores por defecto (si no están en .env)
    DEBUG=(bool, False),
)
# Lee el archivo .env en BASE_DIR/.env
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ── Seguridad y flags de depuración ──
SECRET_KEY = env("SECRET_KEY")           # Obtenido del .env
DEBUG = env.bool("DEBUG")                # Obtenido del .env

# ── Hosts y CSRF ──
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    'https://betterhealthproject.onrender.com',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'BetterHealthProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'BetterHealthProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


# postgresql://URL:PORT@USER:PASSWORD/DB_NAME

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

    # UNCOMMENT THIS FOR PRODUCTION ONLY
    # 'default': dj_database_url.config(
        # Replace this value with your local database's connection string.
    #       default='postgresql://betterhealth_db_user:9lODosx91i41DoB3mJkV5s3HiuAyGAhZ@dpg-d05rs5idbo4c739083l0-a.frankfurt-postgres.render.com/betterhealth_db',
    #       conn_max_age=600
    #   )
}



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# This setting informs Django of the URI path from which your static files will be served to users
# Here, they well be accessible at your-domain.onrender.com/static/... or yourcustomdomain.com/static/...
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_DIRS = [
    BASE_DIR / 'betterhealth/static',
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'betterhealth',

]

# Configuración de API
MUTUA_API = {
    'BASE_URL': env('MUTUA_API_BASE_URL'),
    'USERNAME': env('MUTUA_API_USERNAME'),
    'PASSWORD': env('MUTUA_API_PASSWORD'),
}

LOGIN_REDIRECT_URL = 'home'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
