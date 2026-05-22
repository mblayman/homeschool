import requests
from django.conf import settings

TURNSTILE_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile_token(token: str, remote_ip: str | None = None) -> bool:
    if not token:
        return False

    payload = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        response = requests.post(TURNSTILE_SITEVERIFY_URL, data=payload, timeout=5)
        response.raise_for_status()
        result = response.json()
    except (ValueError, requests.RequestException):
        return False

    return result.get("success") is True
