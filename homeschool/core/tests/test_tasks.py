from homeschool.core.tasks import clear_db_sessions
from homeschool.test import TestCase


class TestClearDBSessions(TestCase):
    def test_run(self):
        """The task can run."""
        clear_db_sessions()
