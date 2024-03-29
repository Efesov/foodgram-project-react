import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Мин.время приготовления рецепта в минутах
MIN_COOKING_TIME = 1
# Макс.время приготовления рецепта в минутах
MAX_COOKING_TIME = 1440
# Мин.кол-во ингредиентов для рецепта
MIN_AMOUNT_INGREDIENTS = 1
# Макс.кол-во ингредиентов для рецепта
MAX_AMOUNT_INGREDIENTS = 1200
# Макс.кол-во ингредиентов для рецепта
PAGE_SIZE = 10

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'groceryassistant.sytes.net']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework.authtoken',
    'rest_framework',
    'django_filters',
    'api.apps.ApiConfig',
    'recipes.apps.RecipesConfig',
    'users.apps.UsersConfig',
    'djoser',
]

AUTH_USER_MODEL = 'users.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodgram.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'foodgram.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'django'),
        'USER': os.getenv('POSTGRES_USER', 'django'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', 5432)
    }
}

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


LANGUAGE_CODE = 'ru'

TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = os.getenv('USE_TZ')

STATIC_URL = '/static_backend/'
STATIC_ROOT = BASE_DIR / 'collect_static'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    "DEFAULT_PAGINATION_CLASS": "api.pagination.PageLimitPagination",
}

DJOSER = {
    'SERIALIZERS': {
        'user_create': 'api.serializers.UserCreateSerializer',
        'user': 'api.serializers.UserReadSerializer',
        'current_user': 'api.serializers.UserReadSerializer',
    },
    'HIDE_USERS': False,
    'PERMISSIONS': {
        'user': [
            'rest_framework.permissions.IsAuthenticatedOrReadOnly'
        ],
        'user_list': [
            'rest_framework.permissions.IsAuthenticatedOrReadOnly'
        ],
    },
}

DATA_ROOT = os.path.join(BASE_DIR, 'data')
