#!/usr/bin/env python

from enum import IntEnum
import pandas as pd
import numpy as np
import sys
import argparse
import math
import glob
import os
import ntpath

# read the pwm from an external file
def read_pwm(filename, model_order, read_order):
    # for IUPAC presentation of 0th order contribution of a higher order model input file, only read every other order+1 line
    elements = pow(4, (read_order + 1))
    skipper = model_order + 1 + read_order
    pwm = []
    with open(filename) as fh:
        for line in fh:
            if skipper == model_order + 1:
                profile = np.zeros(elements)
                tokens = line.split()
                if len(tokens) != elements:
                    print("ERROR: line does not seem to be part of a valid pwm:due to length!!!", file=sys.stderr)
                    print("\t{}".format(line), file=sys.stderr)
                    # exit(1)
                for i, token in enumerate(tokens):
                    profile[i] = float(token)
                EPSILON = 0.1 * (read_order + 1)
                if np.sum(profile) >= pow(4, read_order) + EPSILON or np.sum(profile) <= pow(4, read_order) - EPSILON:
                    print("ERROR: line does not seem to be part of a valid pwm: due to sum!!!", file=sys.stderr)
                    print("\t{}".format(line), file=sys.stderr)
                    print(np.sum(profile))
                    # exit(1)
                pwm.append(profile)
            if skipper == read_order:
                skipper = model_order + 1 + read_order
            else:
                skipper = skipper - 1
    return pwm


def read_bg(bg_file, pwm_order, width):
    pwm = []
    with open(bg_file) as fh:
        for line in fh:
            if line.split()[0] == "#":
                if line.split()[1] == "K":
                    bg_model_order = int(line.split()[3])
                    elements = pow(4, (pwm_order + 1))
                    skipper = bg_model_order + 1 + pwm_order
                    if bg_model_order < pwm_order:
                        print("ERROR: Background model order is lower than pwm_order !!!", file=sys.stderr)
                        print("\t{}".format(line), file=sys.stderr)
                        pwm_order = bg_model_order
                        elements = pow(4, (pwm_order + 1))
                        skipper = bg_model_order + 1 + pwm_order
            else:
                if skipper == bg_model_order + 1:
                    profile = np.zeros(elements)
                    tokens = line.split()
                    if len(tokens) != elements:
                        print("ERROR: line does not seem to be part of a valid pwm:due to length!!!", file=sys.stderr)
                        print("\t{}".format(line), file=sys.stderr)
                        # exit(1)
                    for i, token in enumerate(tokens):
                        profile[i] = float(token)
                    EPSILON = 0.1 * (pwm_order + 1)
                    if np.sum(profile) >= pow(4, pwm_order) + EPSILON or np.sum(profile) <= pow(4,
                                                                                                 pwm_order) - EPSILON:
                        print("ERROR: line does not seem to be part of a valid pwm: due to sum!!!", file=sys.stderr)
                        print("\t{}".format(line), file=sys.stderr)
                        print(np.sum(profile))
                        # exit(1)
                    for n in range(width):
                        pwm.append(profile)
                    break
                else:
                    skipper = skipper - 1
    return pwm

# calculate min distance between two pwms of different length
def calculate_pwm_dist(pwm_1, pwm_2, offset1, offset2, overlap_len):
    dist = 0
    for i in range(0, overlap_len):
        for a in range(0, 16):
            dist = dist + (pwm_1[offset1 + i][a] - pwm_2[offset2 + i][a]) * (
            math.log(pwm_1[offset1 + i][a], 2) - math.log(pwm_2[offset2 + i][a], 2))
    return dist

def get_min_dist(p_pwm, q_pwm):
    len_p = len(p_pwm)
    len_q = len(q_pwm)
    max_overlap = min(len_p-20, len_q-20)
    min_dist = 10e6
    min_W = 0
    min_offset_p = 0
    min_offset_q = 0
    for offset_p in range(10, (len_p - 11)):
        W = min(max_overlap, len_p - offset_p)
        dist = calculate_pwm_dist(p_pwm, q_pwm, offset_p, 10, W)
        if dist < min_dist:
            min_dist = dist
            min_W = W
            min_offset_p = offset_p
    for offset_q in range(10, (len_q - 11)):
        W = min(max_overlap, len_q - offset_q)
        dist = calculate_pwm_dist(p_pwm, q_pwm, 10, offset_q, W)
        if dist < min_dist:
            min_dist = dist
            min_W = W
            min_offset_p = 0
            min_offset_q = offset_q
    return (min_dist, min_W, min_offset_p, min_offset_q)


def get_scores(pwm, pwm_bg, db_folder, db_order, read_order):
    # Loop over database
    info = pd.DataFrame()
    for entry in glob.iglob(os.path.join(db_folder + '/**/*.ihbcp'), recursive=True):
        # read pwm
        pwmDB = read_pwm(entry, db_order, read_order)
        # check if gb_model needs to be shortened
        if len(pwmDB) < len(pwm):
            # truncate pwm_bg
            pwm_bg = pwm_bg[:][0:len(pwmDB)]
        # calculate min distances
        (dist_p_bg, W_p_bg, offset_p_bg, offset_bg_p) = get_min_dist(pwm, pwm_bg)
        (dist_q_bg, W_q_bg, offset_q_bg, offset_bg_q) = get_min_dist(pwmDB, pwm_bg)
        (dist_p_q, W, offset_p, offset_q) = get_min_dist(pwm, pwmDB)
        # calculate matching score
        s_p_q = dist_p_bg + dist_q_bg - dist_p_q
        print(str.split(ntpath.basename(entry), "_")[0])
        dat = pd.Series({'Name': str.split(ntpath.basename(entry), "_")[0],
                         'score': s_p_q,
                         'W': W,
                         'offset_p': offset_p,
                         'offset_q': offset_q,
                         'dist': dist_p_q,
                         'dist_p_bg': dist_p_bg,
                         'dist_q_bg': dist_q_bg,
                         'p_value': np.nan,
                         'e_value': np.nan })
        info = info.append(dat, ignore_index=True)
    return info

def shuffle_pwm(pwm):
    shuffled_pwm = np.random.permutation(pwm)
    return shuffled_pwm


def calclate_p_and_e_value(info_real, info_all,q , p_val_limit):

    # sort matches by scores
    info = info_all.sort_values(by='score', ascending=[0, ])
    info = info.reset_index()
    N = round(len(info) * q)

    # find sq
    sq = info['score'][N]

    a = 1 / (sum(info['score'][0 :  N] - sq) / N)

    for i in range(len(info_real)):
        p_val_s = q * math.exp(- (info_real['score'][i] - sq) * a)
        info_real['p_value'][i] = p_val_s
        e_val_s = N * p_val_s
        info_real['e_value'][i] = e_val_s

    return info_real[:][info_real['p_value']< p_val_limit]

# THE main ;)
def main():
    parser = argparse.ArgumentParser(description='Translates a PWM into an IUPAC identifier and prints it')
    parser.add_argument(metavar='PWM_FILE', dest='pwm_file', type=str,
                        help='file with the pwm')
    parser.add_argument(metavar='BG_FILE', dest='bg_file', type=str,
                        help='file with the background model')
    parser.add_argument(metavar='DB_FOLDER', dest='db_folder', type=str,
                        help='folder to search for database match')
    parser.add_argument(metavar='PWM_ORDER', dest='pwm_order', type=int,
                        help='order of the model represented in the pwm file')
    parser.add_argument(metavar='DB_ORDER', dest='db_order', type=int, default=4,
                        help='order of database models')
    parser.add_argument(metavar='READ_ORDER', dest='read_order', type=int, default=1,
                        help='order for comparison needs to be lower or equal db /pwm order')
    parser.add_argument(metavar='SHUFFLE_TIMES', dest='shuffle_times', type=int, default=10,
                        help='how often to shuffle the pwm for the bakcground distribution')
    parser.add_argument(metavar='P_VAL_LIMIT', dest='p_val_limit', type=float, default=0.1,
                        help='report matches up to p_val_limit')
    parser.add_argument(metavar='QUANTILE_OF_INTEREST', dest='quantile_of_interest', type=float, default=0.1,
                        help='which top percent to use for the function estimation')

    #pwm_file = "/home/kiesel/Desktop/TomTomTool/BaMMOutput/wgEncodeOpenChromChipMcf7CtcfAlnRep0_summits125_motif_1.ihbcp"
    #bg_file = "/home/kiesel/Desktop/TomTomTool/BaMMOutput/wgEncodeOpenChromChipMcf7CtcfAlnRep0_summits104_restr5000.hbcp"
    #db_folder = "/home/kiesel/Desktop/MARVIN_BACKUP/Results/"

    args = parser.parse_args()

    # 1. get real infos
    # read pwm
    pwm = read_pwm(args.pwm_file, 4, 1)
    pwm_bg = read_bg(args.bg_file, args.pwm_order, len(pwm))
    info_real = get_scores(pwm, pwm_bg, args.db_folder, args.db_order, args.read_order)

    # 2. get x-times shuffled info and concatenate to calculate p_and_e_value
    frames = [info_real]
    for x in range(args.shuffle_times):
        pwm_shuff = shuffle_pwm(pwm)
        info_fake = get_scores(pwm_shuff, pwm_bg, args.db_folder, args.db_order, args.read_order)
        frames.append(info_fake)

    # 3. concatenate all and calculate pvalues and evalues for the entries
    info_all = pd.concat(frames)

    best_reals = calclate_p_and_e_value(info_real, info_all, args.quantile_of_interest, args.p_val_limit)

    print('%s' % '\n '.join(map(str, best_reals['Name'])))

#best_reals_by_W = best_reals.sort_values(by='W', ascending=[0, ])
#best_reals_by_score = best_reals.sort_values(by='score', ascending=[0, ])
#best_reals_by_dist = best_reals.sort_values(by='dist', ascending=[1, ])
#best_reals_by_pval = best_reals.sort_values(by='p_value', ascending=[1, ])

# if called as a script; calls the main method
if __name__ == '__main__':
    main()

