import functools

import bleach

strip_clean = functools.partial(bleach.clean, strip=True)


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
