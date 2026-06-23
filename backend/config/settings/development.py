from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Use SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
