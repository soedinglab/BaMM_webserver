from bammmotif.utils.motif_db_sync import sync_databases
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        sync_databases(settings.MOTIF_DATABASE_PATH)
