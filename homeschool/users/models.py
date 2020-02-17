from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.functional import cached_property


class User(AbstractUser):
    """A custom user for extension"""

    @cached_property
    def school(self):
        return self.school_set.latest("id")

    def get_local_today(self):
        """Get the current date from the user's timezone point of view.

        Use tz_detect so that localdate is pulling the current timezone
        from the session.
        """
        return timezone.localdate()
