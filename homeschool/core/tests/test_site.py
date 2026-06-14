import warnings

from django.forms import URLField

from homeschool.core.site import full_url_reverse
from homeschool.test import TestCase


class TestFullURLReverse(TestCase):
    def test_builds_url(self):
        """The utility builds a URL that includes the scheme and site."""
        url = full_url_reverse("core:terms")
        assert url == "http://example.com/terms/"


class TestURLFieldDefaults(TestCase):
    def test_default_scheme_is_https(self):
        """Project settings opt into Django's HTTPS URL default."""
        with warnings.catch_warnings(record=True) as captured:
            field = URLField()

        assert field.assume_scheme == "https"
        assert captured == []
