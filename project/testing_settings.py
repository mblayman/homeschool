from django.contrib.auth.hashers import BasePasswordHasher

from .settings import *  # noqa

# An in-memory database should be good enough for now.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# Use regular files instead of S3 for tests.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # Whitenoise does not play well with tz_detect
        # because tests don't run collectstatic.
        # Override back to the default storage for testing.
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Make sure that tests are never sending real emails.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


# The password hasher is deliberately slow on the real site. Use a dumb and fast one.
class SimplePasswordHasher(BasePasswordHasher):
    """A simple hasher inspired by django-plainpasswordhasher"""

    algorithm = "dumb"  # This attribute is needed by the base class.

    def salt(self):
        return ""

    def encode(self, password, salt):
        return "dumb$$%s" % password

    def verify(self, password, encoded):
        algorithm, hash = encoded.split("$$", 1)
        assert algorithm == "dumb"
        return password == hash

    def safe_summary(self, encoded):
        """This is a decidedly unsafe version. The password is returned in the clear."""
        return {"algorithm": "dumb", "hash": encoded.split("$", 2)[2]}


PASSWORD_HASHERS = ("project.testing_settings.SimplePasswordHasher",)

# This eliminates the warning about a missing staticfiles directory.
WHITENOISE_AUTOREFRESH = True
