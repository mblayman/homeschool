import datetime

from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from homeschool.accounts import constants
from homeschool.accounts.models import Account


@db_periodic_task(crontab(minute="0", hour="0"))
def expire_trials():
    """Expire any accounts that are TRIALING beyond the trial days limit"""
    print("Search for old trial accounts...")
    # Give an extra day to be gracious and avoid customer complaints.
    cutoff_days = constants.TRIAL_DAYS + 1
    trial_cutoff = timezone.now() - datetime.timedelta(days=cutoff_days)
    expired_trials = Account.objects.filter(
        status=Account.AccountStatus.TRIALING, user__date_joined__lt=trial_cutoff
    )
    count = expired_trials.update(status=Account.AccountStatus.TRIAL_EXPIRED)
    print(f"Expired {count} trial(s)")
