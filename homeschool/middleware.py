import html

import bleach
from django.conf import settings
from whitenoise.middleware import WhiteNoiseMiddleware


class MoreWhiteNoiseMiddleware(WhiteNoiseMiddleware):
    def __init__(self, get_response=None, settings=settings):
        super().__init__(get_response, settings=settings)
        self.add_files("blog_out", prefix="blog/")


def strip_clean(input_text):
    """Strip out undesired tags.

    This removes tags like <script>, but leaves characters like & unescaped.
    The goal is to store the raw text in the database with the XSS nastiness.
    By doing this, the content in the database is raw
    and Django can continue to assume that it's unsafe by default.
    """
    return html.unescape(bleach.clean(input_text, strip=True))


class SqueakyCleanMiddleware:
    """Bleach all fields in POST data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.POST:
            # Update the POST QueryDict in place.
            request.POST._mutable = True

            # Clean the fields.
            for field_name, field_values in request.POST.lists():
                request.POST.setlist(field_name, map(strip_clean, field_values))

            # Seal the POST back up.
            request.POST._mutable = False
        return self.get_response(request)
