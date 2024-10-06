from importlib import import_module

from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import db_periodic_task


@db_periodic_task(crontab(minute="0", hour="0"))
def clear_db_sessions():
    print("Clear expired sessions")
    engine = import_module(settings.SESSION_ENGINE)
    engine.SessionStore.clear_expired()
