from homeschool.core.site import full_url_reverse
from homeschool.test import TestCase


class TestFullURLReverse(TestCase):
    def test_builds_url(self):
        """The utility builds a URL that includes the scheme and site."""
        url = full_url_reverse("core:terms")
        assert url == "http://example.com/terms/"
