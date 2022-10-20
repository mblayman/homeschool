import json

import pytest
import requests
import responses
from django.conf import settings
from django.test import override_settings

from homeschool.core.slack_gateway import SlackGateway
from homeschool.test import TestCase


class TestSlackGateway(TestCase):
    @responses.activate
    @override_settings(SLACK_WEBHOOK="https://testserver")
    def test_send_message(self):
        """The gateway posts a message to the webhook."""
        responses.add(responses.POST, settings.SLACK_WEBHOOK)
        gateway = SlackGateway()

        gateway.send_message("success")

        assert json.loads(responses.calls[0].request.body) == {"text": "success"}

    @responses.activate
    @override_settings(SLACK_WEBHOOK="https://testserver")
    def test_send_message_timeout(self):
        """The gateway records a request failure."""
        responses.add(
            responses.POST, settings.SLACK_WEBHOOK, body=requests.exceptions.Timeout()
        )
        gateway = SlackGateway()

        with pytest.raises(requests.RequestException):
            gateway.send_message("fails")


def test_print(capsys):
    """Without the webhook URL, output is printed."""
    gateway = SlackGateway()

    gateway.send_message("success")

    assert "success" in capsys.readouterr().out
