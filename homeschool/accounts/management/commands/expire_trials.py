import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from homeschool.accounts import constants
from homeschool.accounts.models import Account


class Command(BaseCommand):
    help = "Expire any accounts that are TRIALING beyond the trial days limit"

    def handle(self, *args, **kwargs):
        self.stdout.write("Search for old trial accounts...")
        # Give an extra day to be gracious and avoid customer complaints.
        cutoff_days = constants.TRIAL_DAYS + 1
        trial_cutoff = timezone.now() - datetime.timedelta(days=cutoff_days)
        expired_trials = Account.objects.filter(
            status=Account.AccountStatus.TRIALING, user__date_joined__lt=trial_cutoff
        )
        count = expired_trials.update(status=Account.AccountStatus.TRIAL_EXPIRED)
        self.stdout.write(f"Expired {count} trial(s)")
