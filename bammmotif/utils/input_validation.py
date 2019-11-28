import subprocess
import re
from Bio.motifs import minimal

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


class FileFormatValidationError(ValueError):
    pass


def validate_generic_meme(meme_file):
    try:
        return validate_generic_meme_textfile(meme_file)
    except UnicodeDecodeError:
        raise FileFormatValidationError('does not seem to be a text file')


def validate_generic_meme_textfile(meme_file):
    with open(meme_file) as handle:
        line = handle.readline()
        if line.strip() != 'MEME version 4':
            raise FileFormatValidationError('requires MEME minimal file format version 4')

        # skip over all optional info
        while line and line != 'Background letter frequencies\n':
            line = handle.readline()

        if line != 'Background letter frequencies\n':
            raise FileFormatValidationError('could not find background frequencies')

        bg_toks = handle.readline().split()[1::2]
        try:
            [float(f) for f in bg_toks]
        except ValueError:
            raise FileFormatValidationError('background frequencies malformed')

        # parse pwms
        width_pat = re.compile(r'w= (\d+)')

        for line in handle:
            if line.startswith('MOTIF '):
                motif_id = line.split()[1]

                info_line = handle.readline()
                width_hit = width_pat.search(info_line)
                if not width_hit:
                    raise FileFormatValidationError('could not find motif width of motif %s' % motif_id)
                pwm_length = int(width_hit.group(1))
                try:
                    for i in range(pwm_length):
                        [float(p) for p in handle.readline().split()]
                except ValueError:
                    raise FileFormatValidationError('could not parse PWM of motif %s' % motif_id)
    
    # additional layer: parse file with biopython
    with open(meme_file) as handle:
        try:
            records =  minimal.read(f)
        except:
            raise FileFormatValidationError('did not pass meme-minimal file format validation')


def validate_bamm_file(file_path, homogeneous=False):
    with open(file_path) as file:
        try:
            contents = file.read(52428800)
            if file.readline():
                raise FileFormatValidationError('input file too large to be read into memory')
        except UnicodeDecodeError:
            raise FileFormatValidationError('does not seem to be a text file')
        return validate_bamm_string(contents, homogeneous)


def validate_bamm_string(text, homogeneous=False):
    text = text.strip('\n')
    for block_no, block in enumerate(text.split('\n\n')):
        block_probs = []
        for line in block.split('\n'):
            if line.startswith('#'):
                continue
            block_probs.append(line.split())

        for order, kmer_probs in enumerate(block_probs):
            validate_order_len(kmer_probs, order)
            validate_probabilities(kmer_probs)

    if homogeneous and block_no > 0:
        raise FileFormatValidationError('expected background model, but got motif model')
    return True


# TODO currently deactivated
MAX_PROB_EPSILON = 10000000


def validate_probabilities(probs):
    all_probs = []
    for prob_str in probs:
        try:
            prob = float(prob_str)
            if not 0 <= prob <= 1 + MAX_PROB_EPSILON:
                raise ValueError()
        except ValueError:
            raise FileFormatValidationError('malformed probability representation: %s' % prob_str)
        all_probs.append(prob)


def validate_order_len(probs, order, alphabet_size=4):
    n_kmers = alphabet_size ** (order + 1)
    if len(probs) != n_kmers:
        raise FileFormatValidationError('unexpected number of probabilities  %s' % probs)
