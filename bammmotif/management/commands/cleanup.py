from bammmotif.utils.cleanup import full_cleanup
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        full_cleanup()
