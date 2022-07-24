from django.http import HttpResponse
from django.urls import include, path


def a_root_view(request):
    return HttpResponse()  # pragma: no cover


urlpatterns = [
    path("root-view/", a_root_view, name="test-root-view"),
    path("nested/", include("homeschool.denied.tests.nested_urls")),
]
