from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse


def full_url_reverse(url_name):
    """Generate a URL that includes scheme and site name."""
    scheme = "https://" if settings.IS_SECURE else "http://"
    site = get_current_site(request=None)
    url = reverse(url_name)
    return f"{scheme}{site}{url}"
