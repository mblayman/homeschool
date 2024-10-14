from pathlib import Path

import environs

BASE_DIR = Path(__file__).resolve().parent.parent

env = environs.Env()
env.read_env()

SECRET_KEY = env.str("SECRET_KEY")

DEBUG = env.bool("DEBUG", False)
DEBUG_TOOLBAR = env.bool("DEBUG_TOOLBAR", False)

ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", [])

# App constants
domain = "theschooldesk.app"

# Application definition

INSTALLED_APPS = [
    # Load Sentry early to initialize it.
    "homeschool.sentry",
    "project.apps.AdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_extensions",
    "django_htmx",
    "djstripe",
    "hijack",
    "hijack.contrib.admin",
    "huey.contrib.djhuey",
    "ordered_model",
    "simple_history",
    "tz_detect",
    "waffle",
    "homeschool.accounts",
    "homeschool.core",
    "homeschool.courses",
    "homeschool.notifications",
    "homeschool.referrals",
    "homeschool.reports",
    "homeschool.schools",
    "homeschool.students",
    "homeschool.teachers",
    "homeschool.users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "homeschool.middleware.MoreWhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "tz_detect.middleware.TimezoneMiddleware",
    "homeschool.middleware.SqueakyCleanMiddleware",
    "denied.middleware.DeniedMiddleware",
    "homeschool.accounts.middleware.AccountGateMiddleware",
]

# Enable the debug toolbar only in DEBUG mode.
if DEBUG and DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

ROOT_URLCONF = "project.urls"

TEMPLATES: list = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# As of Django 4.1, the cached loader is used in development mode.
# runserver works around this in some manner, but Gunicorn does not.
# Override the loaders to get non-cached behavior.
if DEBUG:
    # app_dirs isn't allowed to be True when the loaders key is present.
    TEMPLATES[0]["APP_DIRS"] = False
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]

WSGI_APPLICATION = "project.wsgi.application"

# Auth
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"  # noqa
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "core:dashboard"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env.path("DB_DIR", BASE_DIR) / "db.sqlite3",
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=wal;",
        },
    }
}
# Starting in Django 3.2, the default field is moving to BigAutoField,
# but I don't want to mess with a bunch of migrations in 3rd party apps.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Email
EMAIL_BACKEND = env.str("EMAIL_BACKEND", "anymail.backends.sendgrid.EmailBackend")
# Enable this to test with MailHog for local email testing.
if env.bool("EMAIL_TESTING", False):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "0.0.0.0"  # noqa: S104 This is for local testing only. It's ok.
    EMAIL_PORT = 1025
DEFAULT_FROM_EMAIL = f"noreply@{domain}"
SERVER_EMAIL = f"noreply@{domain}"

# Files
STORAGES = {
    "default": {
        "BACKEND": env.str(
            "DEFAULT_FILE_STORAGE", "storages.backends.s3boto3.S3Boto3Storage"
        ),
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
MEDIA_ROOT = str(BASE_DIR / "media/")
MEDIA_URL = "/media/"

# Forms
# This setting lets Django form widget templates be used or overridden.
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        # Weasyprint is pretty noisy about CSS stuff generated by Tailwind
        # that it doesn't understand (e.g., CSS variables).
        "weasyprint": {"level": "ERROR", "propagate": False},
    },
}

# Security
# Some of these are configurable settings because local development is done
# over HTTP. If local development is ever switched to HTTPS, then it would
# be good to enable the settings all the time.
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "same-origin"
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", 60 * 60 * 24 * 365)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# The health check was failing with a 301 to HTTPS.
# With kamal-proxy in front and the .app domain, this should not be needed.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", True)

SILENCED_SYSTEM_CHECKS: list[str] = [
    # STRIPE_TEST_SECRET_KEY and STRIPE_LIVE_SECRET_KEY settings exist
    # and djstripe wants them not to exist.
    "djstripe.I002",
    # Disable warning about SECURE_SSL_REDIRECT.
    # The combo of kamal-proxy using Let's Encrypt and the `.app` domain
    # only working with HTTPS means that the warning can be ignored safely.
    "security.W008",
]

# Sessions
# Allow users to be logged in for a month.
SESSION_COOKIE_AGE = 30 * 24 * 60 * 60

# django.contrib.sites
SITE_ID = 1

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# 3rd party packages

# django-allauth
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/start/"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = env.str(
    "ANYMAIL_ACCOUNT_DEFAULT_HTTP_PROTOCOL", "https"
)
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "School Desk - "
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGOUT_REDIRECT_URL = "core:index"
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_DISPLAY = lambda user: user.email  # noqa
ACCOUNT_USERNAME_REQUIRED = False

# django-anymail
ANYMAIL = {"SENDGRID_API_KEY": env.str("SENDGRID_API_KEY")}

# django-hashid-field
HASHID_FIELD_SALT = env.str("HASHID_FIELD_SALT")

# django-hijack
HIJACK_LOGOUT_REDIRECT_URL = "/office/users/user/"

# django-storages
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", "school-desk")

# django-waffle
WAFFLE_FLAG_MODEL = "core.Flag"
WAFFLE_CREATE_MISSING_FLAGS = True

# dj-stripe
STRIPE_LIVE_SECRET_KEY = env.str("STRIPE_LIVE_SECRET_KEY")
STRIPE_TEST_SECRET_KEY = env.str("STRIPE_TEST_SECRET_KEY")
STRIPE_LIVE_MODE = env.bool("STRIPE_LIVE_MODE", True)
STRIPE_PUBLISHABLE_KEY = (
    env.str("STRIPE_LIVE_PUBLISHABLE_KEY")
    if STRIPE_LIVE_MODE
    else env.str("STRIPE_TEST_PUBLISHABLE_KEY")
)
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
DJSTRIPE_SUBSCRIBER_MODEL = "accounts.Account"
DJSTRIPE_USE_NATIVE_JSONFIELD = True
DJSTRIPE_WEBHOOK_SECRET = env.str("DJSTRIPE_WEBHOOK_SECRET")
# dj-stripe won't accept an empty string to disable validation
# so the logic has to be conditional.
djstripe_webhook_validation = env.str("DJSTRIPE_WEBHOOK_VALIDATION", "verify_signature")
DJSTRIPE_WEBHOOK_VALIDATION = (
    djstripe_webhook_validation if djstripe_webhook_validation else None
)

# When the validation is explicitly disabled (i.e., dev mode),
# the check should be ignored to appease CI.
if DJSTRIPE_WEBHOOK_VALIDATION is None:
    SILENCED_SYSTEM_CHECKS.append("djstripe.W004")

# Huey
HUEY = {
    "huey_class": "huey.SqliteHuey",
    "filename": env.path("DB_DIR", BASE_DIR) / "huey.sqlite3",
    "immediate": False,
}

# Sentry
SENTRY_ENABLED = env.bool("SENTRY_ENABLED", True)
SENTRY_DSN = env.str("SENTRY_DSN")

# WhiteNoise
WHITENOISE_INDEX_FILE = True

# App settings

# Is the app in a secure context or not?
IS_SECURE = env.bool("IS_SECURE", True)

# Add extra output directories that WhiteNoise can serve as static files
# *outside* of `staticfiles`.
MORE_WHITENOISE = [
    {"directory": BASE_DIR / "blog_out", "prefix": "blog/"},
    {"directory": BASE_DIR / "docs" / "_build" / "html", "prefix": "docs/"},
]

# accounts
ACCOUNT_GATE_ALLOW_LIST = [
    "/accounts/logout/",
    "/help/",
    "/subscriptions/create-checkout-session/",
]
ACCOUNTS_MONTHLY_PRICE_NICKNAME = "monthly-v1"
ACCOUNTS_ANNUAL_PRICE_NICKNAME = "annual-v1"
ACCOUNTS_PRICE_NICKNAMES = (
    ACCOUNTS_MONTHLY_PRICE_NICKNAME,
    ACCOUNTS_ANNUAL_PRICE_NICKNAME,
)

# core
SLACK_WEBHOOK = env.str("SLACK_WEBHOOK", "")
SUPPORT_EMAIL = f"support@{domain}"
