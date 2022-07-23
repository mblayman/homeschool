from django.test import RequestFactory

from homeschool.denied.middleware import DeniedMiddleware
from homeschool.test import TestCase, get_response


class TestDeniedMiddleware(TestCase):
    rf = RequestFactory()

    def test_unbroken_chain(self):
        """The middleware continues the chain."""
        request = self.rf.get("/")
        middleware = DeniedMiddleware(get_response)

        response = middleware(request)

        assert response.status_code == 200

    def test_default_forbidden(self):
        """A view is denied by default."""
        request = self.rf.get("/")
        middleware = DeniedMiddleware(get_response)

        response = middleware.process_view(request, get_response, [], {})

        assert response.status_code == 403
