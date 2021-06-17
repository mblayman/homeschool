from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from homeschool.referrals.models import Referral


class Command(BaseCommand):
    help = "Send any PENDING referral emails"

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetch pending referrals to send...")

        sent_count = 0
        pending_referrals = Referral.objects.filter(status=Referral.Status.PENDING)
        for referral in pending_referrals:
            sent_count += send_mail(
                subject="A friend has invited to try School Desk!",
                message="this is the message",
                from_email=None,
                recipient_list=[referral.email],
                html_message="this is the html message",
            )
            referral.status = Referral.Status.SENT
            referral.save()

        self.stdout.write(f"Sent {sent_count} referrals.")
