from django.http import HttpRequest

from homeschool.users.models import User


class AuthenticatedHttpRequest(HttpRequest):
    user: User
