import uuid

from django.core.management.base import BaseCommand, CommandError

from homeschool.accounts.tasks import worker_health_ping


class Command(BaseCommand):
    help = "Verify that the Huey worker can execute queued tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Seconds to wait for worker task completion",
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        token = uuid.uuid4().hex
        result = worker_health_ping(token)

        try:
            value = result.get(blocking=True, timeout=timeout)
        except Exception as exc:
            raise CommandError(
                f"Worker health task did not complete in {timeout}s"
            ) from exc

        if value != token:
            raise CommandError("Worker health task returned unexpected result")

        self.stdout.write(self.style.SUCCESS("Worker health check passed"))
