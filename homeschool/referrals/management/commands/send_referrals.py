from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from homeschool.core.site import full_url_reverse
from homeschool.referrals.models import Referral


class Command(BaseCommand):
    help = "Send any PENDING referral emails"

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetch pending referrals to send...")

        sent_count = 0
        pending_referrals = Referral.objects.filter(status=Referral.Status.PENDING)
        for referral in pending_referrals:
            context: dict = {"account_signup_link": full_url_reverse("account_signup")}
            template = "referrals/email/send_referral"
            text_message = render_to_string(f"{template}.txt", context)
            html_message = render_to_string(f"{template}.html", context)
            sent_count += send_mail(
                subject="A friend has invited to try School Desk!",
                message=text_message,
                from_email=None,
                recipient_list=[referral.email],
                html_message=html_message,
            )
            referral.status = Referral.Status.SENT
            referral.save()

        self.stdout.write(f"Sent {sent_count} referrals.")
