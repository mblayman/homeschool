from homeschool.accounts.models import Account
from homeschool.accounts.tests.factories import AccountFactory
from homeschool.test import TestCase


class TestAccount(TestCase):
    def test_factory(self):
        account = AccountFactory()

        assert account.user is not None
        assert account.status == Account.AccountStatus.BETA
