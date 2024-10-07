from django.core.mail import send_mail
from django.template.loader import render_to_string
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from homeschool.core.site import full_url_reverse
from homeschool.referrals.models import Referral


@db_periodic_task(crontab(minute="0", hour="*/4"))
def send_referrals():
    """Send any PENDING referral emails"""
    print("Fetch pending referrals to send...")

    sent_count = 0
    pending_referrals = Referral.objects.filter(status=Referral.Status.PENDING)
    for referral in pending_referrals:
        context: dict = {"account_signup_link": full_url_reverse("account_signup")}
        template = "referrals/email/send_referral"
        text_message = render_to_string(f"{template}.txt", context)
        html_message = render_to_string(f"{template}.html", context)
        sent_count += send_mail(
            subject="A friend has invited you to try School Desk!",
            message=text_message,
            from_email=None,
            recipient_list=[referral.email],
            html_message=html_message,
        )
        referral.status = Referral.Status.SENT
        referral.save()

    print(f"Sent {sent_count} referrals.")
