import requests
from django.conf import settings


class SlackGateway:
    """An interface to send data to a Slack incoming webhook."""

    timeout = 5

    def send_message(self, message: str) -> None:
        """Send a message."""
        if settings.SLACK_WEBHOOK:
            self._send(message)
        else:
            print(f"Slack message: {message}")

    def _send(self, message):
        """Submit the message data to the webhook."""
        requests.post(
            settings.SLACK_WEBHOOK, json={"text": message}, timeout=self.timeout
        )


slack_gateway = SlackGateway()
