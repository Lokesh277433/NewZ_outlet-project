"""
Django settings for News_outlet project.
"""

import os
from pathlib import Path

from django.template.context_processors import static
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DATA_DIR = Path(os.environ.get('DATA_DIR', BASE_DIR))


def env_int(name, default):
    """Read an integer environment value, falling back safely when it is absent."""
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-)^#-_lz^+66vn1!!&om4^x%nq77!ybfb5026_libg&wmywj2c^',
)

DEBUG = os.environ.get('DJANGO_DEBUG', '1').lower() in ('1', 'true', 'yes')

_allowed = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]

_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(',') if o.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'news',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'News_outlet.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'news.context_processors.live_ticker',
                'news.context_processors.nav_categories',
                'news.context_processors.site_weather',
            ],
        },
    },
]

WSGI_APPLICATION = 'News_outlet.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATA_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-in'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = DATA_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'news:home'
LOGOUT_REDIRECT_URL = 'news:home'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'news-outlet',
    }
}

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = env_int('EMAIL_PORT', 587)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '1').lower() in ('1', 'true', 'yes')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'News Outlet <noreply@newsoutlet.local>')

GNEWS_API_KEY = os.environ.get('GNEWS_API_KEY', '2d6c3cbfebc0ad51d668f38079ba9601')
GNEWS_CACHE_SECONDS = env_int('GNEWS_CACHE_SECONDS', 600)

# OpenWeatherMap current-weather API. Leave the key blank to hide weather.
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')
WEATHER_CITY = os.environ.get('WEATHER_CITY', 'New Delhi')
WEATHER_CACHE_SECONDS = env_int('WEATHER_CACHE_SECONDS', 900)

OTP_EXPIRY_MINUTES = env_int('OTP_EXPIRY_MINUTES', 10)
OTP_RATE_WINDOW_MINUTES = env_int('OTP_RATE_WINDOW_MINUTES', 15)
OTP_MAX_PER_EMAIL = env_int('OTP_MAX_PER_EMAIL', 3)
OTP_MAX_PER_IP = env_int('OTP_MAX_PER_IP', 10)
OTP_MAX_VERIFY_ATTEMPTS = env_int('OTP_MAX_VERIFY_ATTEMPTS', 5)
