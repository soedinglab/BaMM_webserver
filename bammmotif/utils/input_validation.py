import subprocess

FASTA_VALIDATOR_BINARY = 'validate_fasta_file'
BINDINGSITE_VALIDATOR_BINARY = 'validate_bindingsite_file'


class ServerValidationError(Exception):
    pass


def validate_fasta_file(file_path):

    result_description = {
        0: 'Valid fasta file',
        2: 'Cannot read fasta file',
        3: 'Invalid fasta format',
    }

    command = [
        FASTA_VALIDATOR_BINARY,
        '%r' % file_path
    ]
    process = subprocess.run([str(x) for x in command])
    exit_code = process.returncode

    if exit_code < 0:
        raise ServerValidationError('received signal %s' % -exit_code)
    elif exit_code not in result_description:
        raise ServerValidationError('unexpected exit code %s' % exit_code)

    success = exit_code == 0
    return success, result_description[exit_code]


def validate_bindingsite_file(file_path, file_format):

    result_description = {
        0: 'All good.',
        2: 'Cannot open file',
        3: 'Invalid file format',
    }

    command = [
        BINDINGSITE_VALIDATOR_BINARY,
        '%r' % file_path,
        file_format
    ]
    process = subprocess.run([str(x) for x in command])
    exit_code = process.returncode

    if exit_code < 0:
        raise ServerValidationError('received signal %s' % -exit_code)
    elif exit_code not in result_description:
        raise ServerValidationError('unexpected exit code %s' % exit_code)

    success = exit_code == 0
    return success, result_description[exit_code]


def validate_meme_file(file_path):
    return True


def validate_bamm_file(file_path):
    return True


def validate_bamm_bg_file(file_path):
    return True
