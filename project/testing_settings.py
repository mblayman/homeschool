from django.contrib.auth.hashers import BasePasswordHasher

from .settings import *  # noqa

# An in-memory database should be good enough for now.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}


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

# Whitenoise does not play well with tz_detect because tests don't run collectstatic.
# Override back to the default storage for testing.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
