from django.http import HttpResponse
from django.test import RequestFactory

from homeschool.denied.decorators import allow
from homeschool.denied.middleware import DeniedMiddleware
from homeschool.test import TestCase


class TestDeniedMiddleware(TestCase):
    rf = RequestFactory()

    def test_allow(self):
        """An allowed view permits access."""

        @allow
        def allowed_view(request):
            return HttpResponse()

        request = self.rf.get("/")
        middleware = DeniedMiddleware(allowed_view)

        ret = middleware.process_view(request, allowed_view, [], {})

        # The contract of the middleware is that None permits the middleware
        # chain to continue.
        assert ret is None
