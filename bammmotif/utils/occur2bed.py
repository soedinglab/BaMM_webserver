import pandas as pd
import numpy as np
import re


# do not resolve scores that are from p-values <= 10^(-10)
PVAL_SCORE_MAX = 10


def convert_to_bed(occurrence_file, bed_handle):
    df = pd.read_csv(occurrence_file, sep='\t', header=None, skiprows=1,
                     names=['chrom', 'length', 'strand', 'pos', 'pattern', 'p-val', 'e-val'])

    chrom, srange = df['chrom'].str.split(':').str
    _, chrom = chrom.str.split('>').str
    sleft, sright = srange.str.split('-').str
    strand = df['strand']
    mstart, _, mend = df['pos'].str.split('.').str

    sleft = sleft.astype(int)
    sright = sright.astype(int)
    mstart = mstart.astype(int)
    mend = mend.astype(int)
    pattern_lengths = mend - mstart + 1  # patterns are one based

    lengths = df.length.astype(int)
    for i in range(len(chrom)):
        if strand[i] == '+':
            s_start = sleft[i] + mstart[i] - 1
        else:
            s_start = sleft[i] + 2*lengths[i] - mend[i] + 1

        pattern = df['pattern'][i]
        p_value = df['p-val'][i]
        e_value = df['e-val'][i]
        name = '%s|p-value=%.2E|e-value=%.3f' % (pattern, p_value, e_value)
        score = - np.log10(p_value + 1e-10)
        score = min(score, PVAL_SCORE_MAX)
        score = int(score / PVAL_SCORE_MAX * 1000)

        print(chrom[i], s_start, s_start + pattern_lengths[i], name, score, df['strand'][i],
              sep='\t', file=bed_handle)


def is_convertible_to_bed(occurrence_file):
    with open(occurrence_file) as infile:
        infile.readline()
        seq_id, *_ = infile.readline().split()
        if re.match(r'^>[^: ]+:\d+-\d+$', seq_id):
            return True
        return False
