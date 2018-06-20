import inspect
from os import path
import time
import re


class TestFileStorage:

    def __init__(self, root):
        self.root = root

    def __getitem__(self, file_name):
        # get class name and function name of the caller
        stack = inspect.stack()
        frame = stack[1][0]
        fun_name = frame.f_code.co_name

        file_path = path.join(self.root, fun_name, file_name)
        return file_path


SUCCESS_STATUS = 'Success'
ERROR_STATUS = 'Error'
SLEEP_SECONDS = 5


class JobFailureException(Exception):
    pass


def complete_job(job_id, client):
    status = "STARTED"
    while status not in (SUCCESS_STATUS, ERROR_STATUS):
        time.sleep(SLEEP_SECONDS)
        response = client.get('/find_result/%s/status' % job_id)
        status = response.json()['status']

    if status == ERROR_STATUS:
        raise JobFailureException()


re_uuid = re.compile("[0-F]{8}-([0-F]{4}-){3}[0-F]{12}", re.I)


class UuidNotFoundException(Exception):
    pass


def get_job_uuid(content):
    match_obj = re_uuid.match(content)
    if match_obj is not None:
        return match_obj.group(0)
    raise UuidNotFoundException()


def form_to_dict(form):
    params = {}
    for field in form:
        value = field.value()
        if value is not None: 
            params[field.name] = value
    return params
