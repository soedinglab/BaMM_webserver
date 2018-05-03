import subprocess
import re

from django.conf import settings

FASTA_VALIDATOR_BINARY = 'validate_fasta_file'
BINDINGSITE_VALIDATOR_BINARY = 'validate_bindingsite_file'


class ServerValidationError(Exception):
    pass


def validate_fasta_file(file_path):

    result_description = {
        0: 'Valid fasta file',
        2: 'Cannot read fasta file',
        3: 'Invalid fasta format',
        4:  ('Too few sequences in fasta file - expected at least %s'
             % settings.MIN_FASTA_SEQUENCES),
    }

    command = [
        FASTA_VALIDATOR_BINARY,
        file_path,
        settings.MIN_FASTA_SEQUENCES
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


class MEMEValidationError(ValueError):
    pass


def validate_generic_meme(meme_file):
    with open(meme_file) as handle:
        line = handle.readline()
        if line.strip() != 'MEME version 4':
            raise MEMEValidationError('requires MEME minimal file format version 4')

        # skip over all optional info
        while line and line != 'Background letter frequencies\n':
            line = handle.readline()

        if line != 'Background letter frequencies\n':
            raise MEMEValidationError('could not find background frequencies')

        bg_toks = handle.readline().split()[1::2]
        try:
            [float(f) for f in bg_toks]
        except ValueError:
            raise MEMEValidationError('background frequencies malformed')

        # parse pwms
        width_pat = re.compile(r'w= (\d+)')

        for line in handle:
            if line.startswith('MOTIF '):
                motif_id = line.split()[1]

                info_line = handle.readline()
                width_hit = width_pat.search(info_line)
                if not width_hit:
                    raise MEMEValidationError('could not find motif width of motif %s' % motif_id)
                pwm_length = int(width_hit.group(1))
                try:
                    for i in range(pwm_length):
                        [float(p) for p in handle.readline().split()]
                except ValueError:
                    raise MEMEValidationError('could not parse PWM of motif %s' % motif_id)
