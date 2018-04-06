from __future__ import absolute_import
from contextlib import redirect_stdout, redirect_stderr
from .commands import (
    Compress
)

from .utils.misc import (
    JobSaveManager
)

from .utils.path_helpers import (
    get_log_file,
)


def generic_model_zip_task(job):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f), redirect_stderr(f):
                Compress(job)
