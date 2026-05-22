import pytest
import responses
from django.test import override_settings

from homeschool.accounts.forms import SiginForm
from homeschool.accounts.models import User
from homeschool.accounts.turnstile import TURNSTILE_SITEVERIFY_URL


@pytest.mark.usefixtures("db")
class TestSigninForm:
    def test_create_user(self, mailoutbox):
        """A non-existing email creates a new User record."""
        # Check the username uniqueness constraint.
        User.objects.create(email="somethingelse@somewhere.com")
        email = "newuser@somewhere.com"
        data = {"email": email}
        form = SiginForm(data=data)
        is_valid = form.is_valid()

        form.save()
        # Ensure only 1 account is created.
        form.save()

        assert is_valid
        assert User.objects.filter(email=email).count() == 1
        assert mailoutbox

    def test_existing_user(self):
        """When a user account exists for an email, use that user."""
        user = User.objects.create(email="test@testing.com")
        data = {"email": user.email}
        form = SiginForm(data=data)
        is_valid = form.is_valid()

        form.save()

        assert is_valid
        assert User.objects.filter(email=user.email).count() == 1

    def test_invalid_email(self):
        """An invalid email is rejected."""
        data = {"email": "not-an-email"}
        form = SiginForm(data=data)

        is_valid = form.is_valid()

        assert not is_valid
        assert "valid email" in str(form.errors)

    @override_settings(
        TURNSTILE_ENABLED=True,
        TURNSTILE_SITE_KEY="1x00000000000000000000AA",
        TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA",  # noqa: S106
    )
    @responses.activate
    def test_valid_turnstile_token(self, mailoutbox):
        """A valid Turnstile token allows the magic link flow."""
        responses.add(
            responses.POST, TURNSTILE_SITEVERIFY_URL, json={"success": True}, status=200
        )
        data = {
            "email": "newuser@somewhere.com",
            "cf-turnstile-response": "valid-token",
        }
        form = SiginForm(data=data, remote_ip="127.0.0.1")

        assert form.is_valid()

        form.save()

        assert User.objects.filter(email="newuser@somewhere.com").exists()
        assert mailoutbox
        assert len(responses.calls) == 1
        assert "remoteip=127.0.0.1" in responses.calls[0].request.body

    @override_settings(
        TURNSTILE_ENABLED=True,
        TURNSTILE_SITE_KEY="1x00000000000000000000AA",
        TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA",  # noqa: S106
    )
    @responses.activate
    def test_missing_turnstile_token(self, mailoutbox):
        """A missing Turnstile token blocks user creation."""
        data = {"email": "newuser@somewhere.com"}
        form = SiginForm(data=data)

        assert not form.is_valid()

        assert "confirm you are human" in form.non_field_errors()[0]
        assert not User.objects.filter(email="newuser@somewhere.com").exists()
        assert not mailoutbox
        assert len(responses.calls) == 0

    @override_settings(
        TURNSTILE_ENABLED=True,
        TURNSTILE_SITE_KEY="1x00000000000000000000AA",
        TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA",  # noqa: S106
    )
    @responses.activate
    def test_invalid_turnstile_token(self, mailoutbox):
        """An invalid Turnstile token blocks user creation."""
        responses.add(
            responses.POST,
            TURNSTILE_SITEVERIFY_URL,
            json={"success": False},
            status=200,
        )
        data = {
            "email": "newuser@somewhere.com",
            "cf-turnstile-response": "invalid-token",
        }
        form = SiginForm(data=data)

        assert not form.is_valid()

        assert "confirm you are human" in form.non_field_errors()[0]
        assert not User.objects.filter(email="newuser@somewhere.com").exists()
        assert not mailoutbox

    @override_settings(
        TURNSTILE_ENABLED=True,
        TURNSTILE_SITE_KEY="1x00000000000000000000AA",
        TURNSTILE_SECRET_KEY="1x0000000000000000000000000000000AA",  # noqa: S106
    )
    @responses.activate
    def test_turnstile_verification_error(self, mailoutbox):
        """A Turnstile verification error blocks user creation."""
        responses.add(responses.POST, TURNSTILE_SITEVERIFY_URL, status=500)
        data = {
            "email": "newuser@somewhere.com",
            "cf-turnstile-response": "valid-token",
        }
        form = SiginForm(data=data)

        assert not form.is_valid()

        assert "confirm you are human" in form.non_field_errors()[0]
        assert not User.objects.filter(email="newuser@somewhere.com").exists()
        assert not mailoutbox
