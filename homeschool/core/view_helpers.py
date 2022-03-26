from django.contrib import messages
from django.http import HttpRequest, HttpResponseRedirect


def flash_info(request: HttpRequest, message: str, url: str) -> HttpResponseRedirect:
    """Provide an info message and redirect to the URL."""
    messages.info(request, message)
    return HttpResponseRedirect(url)
