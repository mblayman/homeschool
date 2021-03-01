from homeschool.accounts.models import Account, handle_checkout_session_completed
from homeschool.accounts.tests.factories import AccountFactory, EventFactory
from homeschool.test import TestCase


class TestHandleCheckoutSessionCompleted(TestCase):
    def test_account_active(self):
        """An account is set to the active state."""
        account = AccountFactory(status=Account.AccountStatus.TRIALING)
        event = EventFactory(data={"object": {"client_reference_id": str(account.id)}})

        handle_checkout_session_completed(event)

        account.refresh_from_db()
        assert account.status == Account.AccountStatus.ACTIVE
