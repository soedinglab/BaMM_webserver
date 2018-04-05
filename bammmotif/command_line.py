from collections import OrderedDict
import subprocess
import sys
import logging

from django.db import models
from django.core.files import File

from .utils.commandline import CommandlineModule

logger = logging.getLogger(__name__)


class ValidateFasta(CommandlineModule):
    def __init__(self):
        pass


class BammMatch(CommandlineModule):
    def __init__(self):
        pass

class FDRPlotSimple(CommandlineModule):
    def __init__(self):
        pass

class PlotHOBindingSitesLogo(CommandlineModule):
    def __init__(self):
        pass

def zip_files(zipname, file_list):
    zipcmd = 'zip %s %s' % (zipname, " ".join(file_list))
    process = subprocess.Popen(zipcmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ret = process.communicate()
    if process.returncode != 0:
        return False
    sys.stdout.write(ret[0].decode('ascii'))
    return True

def execute_command_get_bg_model_order(params, job):
    command = 'python3 /code/bammmotif/static/scripts/getbgModelOrder.py ' + params
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ret = process.communicate()
    # TODO: What to do if check fails?
    if process.returncode != 0:
        pass
    sys.stdout.write(ret[0].decode('ascii'))
    bg_order = [int(x) for x in ret[0].strip().decode('ascii').split()]
    for val in bg_order:
        job.backgroud_Order = val
        job.save()
        print("BG order = " + str(job.background_Order) + "\n")
        sys.stdout.flush()
    process.wait()
    return job


def transfer_options(job_object, module):
    for key in module.options:
        if hasattr(job_object, key):
            value = job_object.__getattribute__(key)
            if isinstance(value, File):
                if not value.name:
                    value = value.name
                else:
                    value = value.storage.path(value.name)
            if value:
                module.options[key] = value
