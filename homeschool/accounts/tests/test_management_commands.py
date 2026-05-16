from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError

from homeschool.test import TestCase


class TestCheckWorker(TestCase):
    def test_check_worker_command_passes(self):
        call_command("check_worker", timeout=5)

    def test_check_worker_command_errors_when_task_times_out(self):
        class BrokenResult:
            def get(self, *, blocking, timeout):
                raise RuntimeError("no response")

        with patch(
            "homeschool.accounts.management.commands.check_worker.worker_health_ping",
            return_value=BrokenResult(),
        ):
            with self.assertRaisesRegex(
                CommandError, "Worker health task did not complete in 5s"
            ):
                call_command("check_worker", timeout=5)

    def test_check_worker_command_errors_on_wrong_result(self):
        class WrongResult:
            def get(self, *, blocking, timeout):
                return "not-the-token"

        with patch(
            "homeschool.accounts.management.commands.check_worker.worker_health_ping",
            return_value=WrongResult(),
        ):
            with self.assertRaisesRegex(
                CommandError, "Worker health task returned unexpected result"
            ):
                call_command("check_worker", timeout=5)
