import datetime

from django import template
from django.utils import timezone

register = template.Library()


@register.inclusion_tag("accounts/trial_banner.html", takes_context=True)
def trial_banner(context):
    """Show a banner to tell trialing users that their trial is ending soon."""
    context["display_banner"] = False
    account = context["request"].account

    # The banner is only relevant to trials.
    if account.status != account.AccountStatus.TRIALING:
        return context

    trial_banner_start = account.trial_end - datetime.timedelta(days=14)
    if timezone.now() < trial_banner_start:
        # The current time is older than the start, so bail.
        return context

    context["display_banner"] = True
    return context
