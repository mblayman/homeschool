import datetime

from allauth.account.signals import user_signed_up
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property

from homeschool.core.slack_gateway import slack_gateway


# Check https://github.com/typeddjango/django-stubs/issues/1354 for details
class User(AbstractUser):  # type: ignore  # blocked upstream - see above
    """A custom user for extension"""

    @cached_property
    def school(self):
        return self.school_set.latest("id")  # pyright: ignore

    def get_local_today(self) -> datetime.date:
        """Get the current date from the user's timezone point of view.

        Use tz_detect so that localdate is pulling the current timezone
        from the session.
        """
        return timezone.localdate()


class Profile(models.Model):
    """Extra information related to a user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wants_announcements = models.BooleanField(
        default=True,
        help_text="Would you like to receive announcements about new features?",
    )

    def __str__(self):
        return f"Profile for {self.user.username}"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, raw, **kwargs):  # pyright: ignore
    """A new user gets an associated profile."""
    if created and not raw:
        Profile.objects.create(user=instance)


@receiver(user_signed_up, sender=User)
def notify_signup(sender, request, user, **kwargs):  # pyright: ignore
    """Notify that a new signup occurred."""
    slack_gateway.send_message(f"New sign up: {user.username}")
