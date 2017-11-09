from __future__ import unicode_literals

from django.conf import settings
from django.apps import AppConfig

from .utils.motif_db_sync import sync_databases


class BammmotifConfig(AppConfig):
    name = 'bammmotif'

    def ready(self):
        sync_databases(settings.MOTIF_DATABASE_PATH)
