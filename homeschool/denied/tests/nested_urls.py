from django.http import HttpResponse
from django.urls import path


def a_nested_view(request):
    return HttpResponse()  # pragma: no cover


urlpatterns = [
    path("nested-view/", a_nested_view, name="test-nested-view"),
]
