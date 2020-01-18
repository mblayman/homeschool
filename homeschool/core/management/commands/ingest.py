from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ingest CSV data from Homeschool Skedtrack"

    def handle(self, *args, **kwargs):
        self.stdout.write("Read in CSV data")
