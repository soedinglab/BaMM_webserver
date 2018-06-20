import os
import re
import inspect
import importlib
import logging

import requests


from bammmotif.test.utils import (
    TestFileStorage,
    form_to_dict,
)
from bammmotif.bammscan.forms import BaMMScanForm, BaMMScanDBForm
from bammmotif.bamm.forms import OneStepBammJobForm
from bammmotif.peng.forms import PengForm
from bammmotif.mmcompare.forms import MMCompareForm

test_data_root = os.environ.get('TEST_DATA_ROOT', '/test_data')
test_file_storage = TestFileStorage(test_data_root)
server_prefix = os.environ.get('TEST_SERVER_URL')
logger = logging.getLogger(__name__)


def send_post_request(url, params, files):
    client = requests.session()
    client.get(url)
    if 'csrftoken' in client.cookies:
        csrftoken = client.cookies['csrftoken']
    params = {**params}
    params['csrfmiddlewaretoken'] = csrftoken
    response = client.post(url, data=params, files=files, headers=dict(Referer=url))
    return response


def get_bammscan_url():
    url = server_prefix + '/job/bamm_scan/'
    return url


def get_bammscan_db_url(motif_id):
    url = server_prefix + '/job/bamm_scan/db/%s/' % motif_id
    return url


def get_auto_denovo_url():
    url = server_prefix + '/job/denovo/'
    return url


def get_manual_denovo_url():
    url = server_prefix + '/job/seeding/'
    return url


def get_compare_url():
    url = server_prefix + '/job/bamm_compare/'
    return url


def get_auto_denovo_parameters():
    form = OneStepBammJobForm()
    params = form_to_dict(form)
    return params


def get_manual_denovo_parameters():
    form = PengForm()
    params = form_to_dict(form)
    return params


def get_bammscan_parameters():
    form = BaMMScanForm()
    return form_to_dict(form)


def get_bammscan_db_parameters():
    form = BaMMScanDBForm()
    return form_to_dict(form)


def get_compare_parameters():
    form = MMCompareForm()
    return form_to_dict(form)


def _check_status_200(response, test_name=None):
    if not test_name:
        # infer test name with inpect
        stack = inspect.stack()
        frame = stack[1][0]
        test_name = frame.f_code.co_name
    if response.status_code != 200:
        logger.error('obtained status-code %s in test %s' % (response.status_code, test_name))


def _check_successful_submit(response, test_name=None):
    if not test_name:
        # infer test name with inpect
        stack = inspect.stack()
        frame = stack[1][0]
        test_name = frame.f_code.co_name
    content = response.content.decode('utf-8')

    re_uuid = re.compile("[0-F]{8}-([0-F]{4}-){3}[0-F]{12}", re.I)

    only_example = True
    for uuid_match in re_uuid.finditer(content):
        uuid = uuid_match.group(0)
        if not uuid.startswith('00000000-0000-0000-0000'):
            only_example = False

    if only_example:
        logger.error('job submission failed in test %s' % test_name)


def test_denovo():
    params = get_auto_denovo_parameters()
    seq_file = test_file_storage['example.fasta']

    with open(seq_file, 'rb') as seq_handle:
        files = {}
        files['Input_Sequences'] = seq_handle

        url = get_auto_denovo_url()
        response = send_post_request(url, params, files)

    _check_status_200(response)
    _check_successful_submit(response)


def test_manual_denovo():
    params = get_manual_denovo_parameters()
    seq_file = test_file_storage['example.fasta']

    with open(seq_file, 'rb') as seq_handle:
        files = {}
        files['fasta_file'] = seq_handle

        url = get_manual_denovo_url()
        response = send_post_request(url, params, files)

    _check_status_200(response)
    _check_successful_submit(response)


def test_bammscan():
    params = get_bammscan_parameters()
    seq_file = test_file_storage['example.fasta']
    meme_file = test_file_storage['example.meme']

    with open(seq_file, 'rb') as seq_handle, open(meme_file, 'rb') as mod_handle:
        files = {}
        files['Input_Sequences'] = seq_handle
        files['Motif_InitFile'] = mod_handle

        url = get_bammscan_url()
        response = send_post_request(url, params, files)

    _check_status_200(response)
    _check_successful_submit(response)


def test_bammscan_db():
    params = get_bammscan_db_parameters()
    seq_file = test_file_storage['example.fasta']

    with open(seq_file, 'rb') as seq_handle:
        files = {}
        files['Input_Sequences'] = seq_handle

        motif_id = 'GTRD_yeast_v101_0001'
        url = get_bammscan_db_url(motif_id)

        response = send_post_request(url, params, files)

    _check_status_200(response)
    _check_successful_submit(response)


def test_compare():
    params = get_compare_parameters()
    meme_file = test_file_storage['example.meme']

    with open(meme_file, 'rb') as mod_handle:
        files = {}
        files['Motif_InitFile'] = mod_handle

        url = get_compare_url()
        response = send_post_request(url, params, files)

    _check_status_200(response)
    _check_successful_submit(response)


def test_compare_bamm():
    params = get_compare_parameters()
    bg_file = test_file_storage['sox2.hbcp']
    model_file = test_file_storage['sox2_motif_1.ihbcp']

    with open(model_file, 'rb') as mod_handle, open(bg_file, 'rb') as bg_handle:
        files = {}
        files['Motif_InitFile'] = mod_handle
        files['bgModel_File'] = bg_handle

        params['Motif_Init_File_Format'] = 'BaMM'

        url = get_compare_url()
        response = send_post_request(url, params, files)

    _check_status_200(response)
    _check_successful_submit(response)


def test_edd271f9():
    params = get_bammscan_parameters()
    model_file = test_file_storage['sox2_motif_1.ihbcp']
    bg_file = test_file_storage['sox2.hbcp']
    seq_file = test_file_storage['sox2.fasta']

    with open(model_file, 'rb') as mod_handle, open(bg_file, 'rb') as bg_handle,\
            open(seq_file, 'rb') as seq_handle:

        files = {}
        files['Input_Sequences'] = seq_handle
        files['Motif_InitFile'] = mod_handle
        files['bgModel_File'] = bg_handle

        params['Motif_Init_File_Format'] = 'BaMM'

        url = get_bammscan_url()
        response = send_post_request(url, params, files)

    _check_status_200(response)
    _check_successful_submit(response)


def test_19530c7c():
    params = get_compare_parameters()
    bg_file = test_file_storage['sox2.foo.hbcp']
    model_file = test_file_storage['sox2.foo_motif_1.ihbcp']

    with open(model_file, 'rb') as mod_handle, open(bg_file, 'rb') as bg_handle:
        files = {}
        files['Motif_InitFile'] = mod_handle
        files['bgModel_File'] = bg_handle

        params['Motif_Init_File_Format'] = 'BaMM'

        url = get_compare_url()
        response = send_post_request(url, params, files)

    _check_status_200(response)
    _check_successful_submit(response)


def enumerate_tests():
    module = importlib.import_module(__name__)
    functions = inspect.getmembers(module, inspect.isfunction)
    for fun_name, function in functions:
        if fun_name.startswith('test'):
            yield function

def list_tests():
    for test_fun in enumerate_tests():
        print(test_fun.__name__)

def run_tests(selection=[]):
    for test_function in enumerate_tests():
        if not selection:
            test_function()
        else:
            if test_function.__name__ in selection:
                test_function()
