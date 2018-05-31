from __future__ import absolute_import

import os
from celery import Celery
from celery import schedules
from django.conf import settings


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webserver.settings')

app = Celery('webserver')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


SCHEDULE_CLEANUP = schedules.crontab(minute=0, hour=settings.DAILY_CLEANUP_HOUR_UTC)
SCHEDULE_BACKUP = schedules.crontab(minute=0, hour=settings.DAILY_BACKUP_HOUR_UTC)

app.conf.beat_schedule = {
    'cleanup-jobs': {
        'task': 'bammmotif.tasks.cleanup_task',
        'schedule': SCHEDULE_CLEANUP,
        'options': {'queue': 'priority'}
    },
    'backup-jobs': {
        'task': 'bammmotif.tasks.full_backup',
        'schedule': SCHEDULE_BACKUP,
        'options': {'queue': 'priority'}
    },
}
