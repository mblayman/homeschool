from pathlib import Path

import dj_database_url
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    ALLOWED_HOSTS=(list, []),
    ANYMAIL_ACCOUNT_DEFAULT_HTTP_PROTOCOL=(str, "https"),
    AWS_STORAGE_BUCKET_NAME=(str, "school-desk"),
    CSRF_COOKIE_SECURE=(bool, True),
    DATABASE_CONN_MAX_AGE=(int, 600),
    DATABASE_SSL_REQUIRE=(bool, True),
    DEBUG=(bool, False),
    DEBUG_TOOLBAR=(bool, False),
    DJSTRIPE_WEBHOOK_VALIDATION=(str, "verify_signature"),
    EMAIL_BACKEND=(str, "anymail.backends.sendgrid.EmailBackend"),
    EMAIL_TESTING=(bool, False),
    IS_SECURE=(bool, True),
    ROLLBAR_ENABLED=(bool, True),
    ROLLBAR_ENVIRONMENT=(str, "production"),
    SECURE_HSTS_PRELOAD=(bool, True),
    SECURE_HSTS_SECONDS=(int, 60 * 60 * 24 * 365),
    SECURE_SSL_REDIRECT=(bool, True),
    SESSION_COOKIE_SECURE=(bool, True),
    SLACK_WEBHOOK=(str, ""),
    STRIPE_LIVE_MODE=(bool, True),
)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")
DEBUG_TOOLBAR = env("DEBUG_TOOLBAR")

ALLOWED_HOSTS: list[str] = env("ALLOWED_HOSTS")

# App constants
domain = "theschooldesk.app"

# Application definition

INSTALLED_APPS = [
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
    "django_htmx.middleware.HtmxMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "tz_detect.middleware.TimezoneMiddleware",
    "homeschool.middleware.SqueakyCleanMiddleware",
    "homeschool.denied.middleware.DeniedMiddleware",
    "homeschool.accounts.middleware.AccountGateMiddleware",
    "rollbar.contrib.django.middleware.RollbarNotifierMiddleware",
]

# Enable the debug toolbar only in DEBUG mode.
if DEBUG and DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
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
    "default": dj_database_url.config(
        conn_max_age=env("DATABASE_CONN_MAX_AGE"),
        ssl_require=env("DATABASE_SSL_REQUIRE"),
    )
}
# Starting in Django 3.2, the default field is moving to BigAutoField,
# but I don't want to mess with a bunch of migrations in 3rd party apps.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Email
EMAIL_BACKEND = env("EMAIL_BACKEND")
# Enable this to test with MailHog for local email testing.
if env("EMAIL_TESTING"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "0.0.0.0"  # nosec B104: This is for local testing only. It's ok.
    EMAIL_PORT = 1025
DEFAULT_FROM_EMAIL = f"noreply@{domain}"
SERVER_EMAIL = f"noreply@{domain}"

# Files
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
MEDIA_ROOT = str(BASE_DIR / "media/")

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
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "same-origin"
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD")
SECURE_HSTS_SECONDS = env("SECURE_HSTS_SECONDS")
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")

SILENCED_SYSTEM_CHECKS: list[str] = []

# Sessions
# Allow users to be logged in for a month.
SESSION_COOKIE_AGE = 30 * 24 * 60 * 60

# django.contrib.sites
SITE_ID = 1

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 3rd party packages

# django-allauth
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/start/"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = env("ANYMAIL_ACCOUNT_DEFAULT_HTTP_PROTOCOL")
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
ANYMAIL = {"SENDGRID_API_KEY": env("SENDGRID_API_KEY")}

# django-hashid-field
HASHID_FIELD_SALT = env("HASHID_FIELD_SALT")

# django-hijack
HIJACK_LOGOUT_REDIRECT_URL = "/office/users/user/"

# django-storages
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")

# django-waffle
WAFFLE_FLAG_MODEL = "core.Flag"
WAFFLE_CREATE_MISSING_FLAGS = True

# dj-stripe
STRIPE_LIVE_SECRET_KEY = env("STRIPE_LIVE_SECRET_KEY")
STRIPE_TEST_SECRET_KEY = env("STRIPE_TEST_SECRET_KEY")
STRIPE_LIVE_MODE = env("STRIPE_LIVE_MODE")
STRIPE_PUBLISHABLE_KEY = (
    env("STRIPE_LIVE_PUBLISHABLE_KEY")
    if STRIPE_LIVE_MODE
    else env("STRIPE_TEST_PUBLISHABLE_KEY")
)
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
DJSTRIPE_SUBSCRIBER_MODEL = "accounts.Account"
DJSTRIPE_USE_NATIVE_JSONFIELD = True
DJSTRIPE_WEBHOOK_SECRET = env("DJSTRIPE_WEBHOOK_SECRET")
# dj-stripe won't accept an empty string to disable validation
# so the logic has to be conditional.
DJSTRIPE_WEBHOOK_VALIDATION = (
    env("DJSTRIPE_WEBHOOK_VALIDATION") if env("DJSTRIPE_WEBHOOK_VALIDATION") else None
)

# When the validation is explicitly disabled (i.e., dev mode),
# the check should be ignored to appease CI.
if DJSTRIPE_WEBHOOK_VALIDATION is None:
    SILENCED_SYSTEM_CHECKS.append("djstripe.W004")

# rollbar
ROLLBAR = {
    "enabled": env("ROLLBAR_ENABLED"),
    "access_token": env("ROLLBAR_ACCESS_TOKEN"),
    "environment": env("ROLLBAR_ENVIRONMENT"),
    "branch": "main",
    "root": BASE_DIR,
    "capture_email": True,
}

# WhiteNoise
WHITENOISE_INDEX_FILE = True

# App settings

# Is the app in a secure context or not?
IS_SECURE = env("IS_SECURE")

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
SLACK_WEBHOOK = env("SLACK_WEBHOOK")
SUPPORT_EMAIL = f"support@{domain}"
