import sentry_sdk
from django.apps import AppConfig
from django.conf import settings
from sentry_sdk.integrations.django import DjangoIntegration


def traces_sampler(sampling_context):  # pragma: no cover
    """Select a sample rate off of the requested path.

    The root endpoint seemed to get hammered by some bot and ate a huge percent
    of transactions in a week. I don't care about that page right now,
    so ignore it.
    """
    path = sampling_context.get("wsgi_environ", {}).get("PATH_INFO", "")
    if path == "/":
        return 0

    return 1.0


class SentryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "homeschool.sentry"

    def ready(self):  # pragma: no cover
        """Initialize Sentry.

        Sentry initialization is moved to an application ready timeframe
        because it triggers circular imports with settings when used with
        type checking when django-stubs is enabled.
        """
        if not settings.SENTRY_ENABLED:
            return

        sentry_sdk.init(
            dsn="https://7d6332a64c8c4139b7dbbbd96e4e3591@o4504013039992832.ingest.sentry.io/4504013130498048",
            integrations=[
                DjangoIntegration(),
            ],
            traces_sampler=traces_sampler,
            send_default_pii=True,
        )
