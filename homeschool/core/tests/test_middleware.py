from django.http import HttpResponse

from homeschool.middleware import SqueakyCleanMiddleware


def get_response(request):
    """A basic callback for the middleware tests to use."""
    return HttpResponse()


def test_cleans_fields(rf):
    """The middleware bleaches the fields."""
    data = {
        "safe": "No action",
        "badnews": [
            'Oh no! <script>alert("boom");</script>',
            "Another <style>body { color: red; }</style> tag.",
        ],
    }
    request = rf.post("/somewhere/", data=data)
    middleware = SqueakyCleanMiddleware(get_response)

    middleware(request)

    assert not request.POST._mutable
    assert request.POST["safe"] == "No action"
    assert request.POST.getlist("badnews") == [
        'Oh no! alert("boom");',
        "Another body { color: red; } tag.",
    ]
