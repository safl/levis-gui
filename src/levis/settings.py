# Django settings for levis project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Foo To The Bar', 'passport@safl.dk'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'levis.db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Copenhagen'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '=#ve(uowm_y+o*25v8m369&5)ran_@(6n8pzs7v+xo0$bo@gsg'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'levis.urls'

TEMPLATE_DIRS = (
    "/home/safl/Desktop/levis-gui/src/levis/templates"
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "levis.ui.context_processors.menu"
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    
    'dashboard',
    'organization',    
    'helpdesk',    
    'scheduling',
    'accounting',
    'reports',
    'hact'
    
)

MENU_TREE = [
    ('dashboard',       [('normal', 'Dashboard'), ('mini', 'Mini'), ('wall', 'Wall')]),
    ('organization',    [('browse', 'Browse'), ('add', 'Add')]),
    ('helpdesk',        [('browse', 'Browse'), ('add', 'Add')]),
    ('scheduling',      [
        ('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('-','-'),
        ('my_day', 'My Day'), ('my_week', 'My Week'),
        ('my_month', 'My Month'), ('my_agenda', 'My Agenda')
    ]),
    ('accounting',  [('browse', 'Browse')] ),    
    ('reports',     [('browse', 'Browse')] ),
    ('knowledge',   [('browse', 'Browse')] ),
    ('admin',       None ),
]


IMAP_HOST='imap.googlemail.com'
IMAP_PORT=993
IMAP_SSL=True
IMAP_USER='levistest@safl.dk'
IMAP_PASS='LevisTesting.11'
IMAP_POLL=10

POP_HOST='pop.googlemail.com'
POP_PORT=995
POP_SSL=True
POP_USER='levistest@safl.dk'
POP_PASS='LevisTesting.11'
POP_POLL=10

BEANSTALK_HOST='localhost'
BEANSTALK_PORT=11300
