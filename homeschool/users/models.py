from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property


class User(AbstractUser):
    """A custom user for extension"""

    @cached_property
    def school(self):
        return self.school_set.latest("id")
