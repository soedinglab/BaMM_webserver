#!/usr/bin/env python
import matplotlib.pyplot as plt
import argparse
import glob
import math
import ntpath
import os

import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'

# read the pwm from an external file
def read_pwm(filename, model_order, read_order):
    # for IUPAC presentation of 0th order contribution of a higher order model input file, only read every other
    # order+1 line
    elements = pow ( 4, (read_order + 1) )
    skipper = model_order + 1 + read_order
    pwm = []
    with open ( filename ) as fh:
        for line in fh:
            if skipper == model_order + 1:
                profile = np.zeros ( elements )
                tokens = line.split ( )
                if len(tokens) != elements:
                    print("ERROR: line does not seem to be part of a valid pwm:due to length!!!")
                    print("\t{}".format(line))
                    exit(1)
                for i, token in enumerate ( tokens ):
                    profile[i] = float ( token )
                # EPSILON = 0.1 * (read_order + 1)
                # if np.sum(profile) >= pow(4, read_order) + EPSILON or np.sum(profile) <= pow(4, read_order) - EPSILON:
                # print("ERROR: line does not seem to be part of a valid pwm: due to sum!!!", file=sys.stderr)
                # print("\t{}".format(line), file=sys.stderr)
                # print(np.sum(profile))
                # exit(1)
                pwm.append ( profile )
            if skipper == read_order:
                skipper = model_order + 1 + read_order
            else:
                skipper = skipper - 1
    return pwm

def reverseComp( pwm ):
    pwm_rev = []
    for i in range (0, len(pwm) ):
        profile = pwm[i][::-1]
        pwm_rev.append(profile)
    pwm_rev = pwm_rev[::-1]
    return pwm_rev

def read_bg(bg_file, pwm_order, width):
    pwm = []
    bg_model_order = 2
    with open ( bg_file ) as fh:
        for line in fh:
            if line.split ( )[0] == "#":
                if line.split ( )[1] == "K":
                    bg_model_order = min(pwm_order, int ( line.split ( )[3] ))
                    elements = pow ( 4, pwm_order + 1) 
                    skipper = bg_model_order + 1 + pwm_order
            else:
                if skipper == bg_model_order + 1:
                    profile = np.zeros ( elements )
                    tokens = line.split ( )
                    # if len(tokens) != elements:
                    # print("ERROR: line does not seem to be part of a valid pwm:due to length!!!", file=sys.stderr)
                    # print("\t{}".format(line), file=sys.stderr)
                    # exit(1)
                    for i in range( elements ):
                        profile[i] = float ( tokens[i] )
                    # EPSILON = 0.1 * (pwm_order + 1)
                    # if np.sum(profile) >= pow(4, pwm_order) + EPSILON or np.sum(profile) <= pow(4,pwm_order) - EPSILON:
                    # print("ERROR: line does not seem to be part of a valid pwm: due to sum!!!", file=sys.stderr)
                    # print("\t{}".format(line), file=sys.stderr)
                    # print(np.sum(profile))
                    # exit(1)
                    if pwm_order > bg_model_order:
                        # add missing propabilities from lower order
                        for s in range(elements/len(tokens)-1):
                            for i, token in enumerate ( tokens ):
                                profile[i] = float ( token )
                    
                    for n in range ( 0, width ):
                        pwm.append ( profile )
                    break
                else:
                    skipper = skipper - 1
    return pwm


# calculate min distance between two pwms of different length
def calculate_pwm_dist(pwm_1, pwm_2, pwm_1_log, pwm_2_log, offset1, offset2, overlap_len, order):
    dist = 0
    for i in range ( 0, overlap_len ):
        for a in range ( 0, pow(4,order+1)-1 ):
            pwm_avg = (pwm_1[offset1+i][a] + pwm_2[offset2+i][a])/2
            if pwm_avg != 0 & ~np.isnan(pwm_1_log[offset1+i][a]) & ~np.isnan(pwm_2_log[offset2 +i][a]):
                dist = dist + (pwm_1[offset1 + i][a] * pwm_1_log[offset1 +i][a] + pwm_2[offset2 + i][a] * pwm_2_log[offset2 +i][a] - 2 * pwm_avg * math.log(pwm_avg))
            else:
                print( "--->  LOG IS NAN! <----\n")
    return dist


def get_min_dist(p_pwm, q_pwm,p_pwm_log, q_pwm_log, order, min_overlap):
    len_p = len ( p_pwm )
    len_q = len ( q_pwm )
    max_overlap = min ( len_p, len_q )
    min_dist = 10e6
    min_W = 0
    min_offset_p = 0
    min_offset_q = 0
    #min_overlap = round(max_overlap/2)-1
    for offset_p in range ( 0, (len_p - min_overlap) ):
        W = min ( max_overlap, len_p - offset_p )
        dist = calculate_pwm_dist ( p_pwm, q_pwm,  p_pwm_log, q_pwm_log, offset_p, 0, W,order )
        if dist < min_dist:
            min_dist = dist
            min_W = W
            min_offset_p = offset_p
    for offset_q in range ( 0, (len_q - min_overlap) ):
        W = min ( max_overlap, len_q - offset_q )
        dist = calculate_pwm_dist ( p_pwm, q_pwm, p_pwm_log, q_pwm_log, 0, offset_q, W,order )
        if dist < min_dist:
            min_dist = dist
            min_W = W
            min_offset_p = 0
            min_offset_q = offset_q
    return (min_dist, min_W, min_offset_p, min_offset_q)


def get_scores(pwm, pwm_bg, pwm_log, pwm_bg_log, db_folder, db_order, read_order, weight, min_overlap):
    # Loop over database
    (dist_p_bg, W_p_bg, offset_p_bg, offset_bg_p) = get_min_dist ( pwm, pwm_bg, pwm_log, pwm_bg_log, read_order, min_overlap )
    info = pd.DataFrame ( )
    l = 0
    for entry in glob.iglob ( os.path.join ( db_folder + '/**/*.ihbcp' )):
        # read pwm
        pwmDB = read_pwm ( entry, db_order, read_order )
        pwmDB_log = log_pwm(pwmDB)
        # calculate min distances
        (dist_q_bg, W_q_bg, offset_q_bg, offset_bg_q) = get_min_dist ( pwmDB, pwm_bg,pwmDB_log, pwm_bg_log, read_order, min_overlap )
        (dist_p_q, W, offset_p, offset_q) = get_min_dist ( pwm, pwmDB, pwm_log, pwmDB_log, read_order, min_overlap )
        # calculate matching score
        s_p_q = weight*(dist_p_bg + dist_q_bg) - dist_p_q
        # print(str.split(ntpath.basename(entry), "_")[0])
        dat = pd.DataFrame( {'Name': [str.split ( ntpath.basename ( entry ), "_" )[0]],
                           'score': [s_p_q],
                           'W': [W],
                           'offset_p': [offset_p],
                           'offset_q': [offset_q],
                           'dist': [dist_p_q],
                           'dist_p_bg': [dist_p_bg],
                           'dist_q_bg': [dist_q_bg],
                           'p_value': [np.nan],
                           'e_value': [np.nan]} )
        info = info.append(dat, ignore_index=True)
        l = l+1
    return info

def get_selfmatch(info_real, pwm_file):
    # get name
    name = str.split( ntpath.basename(pwm_file), "_")[0]
    return info_real[info_real['Name'] == name]

def shuffle_pwm(pwm):
    shuffled_pwm = np.random.permutation ( pwm )
    return shuffled_pwm


def calclate_p_and_e_value(info_real, info_all, q, p_val_limit):
    # sort matches by scores
    info = info_all.sort_values ( by='score', ascending=[0, ] )
    info = info.reset_index ( )
    N = round ( len ( info ) * q )
    # find sq
    sq = info['score'][N]
    a = 1 / (sum ( info['score'][0:N] - sq ) / N)
    for i in range(0,len(info_real)):
        p_val_s = q * math.exp ( - (info_real['score'][i] - sq) * a )
        info_real.loc[i,'p_value'] = p_val_s
        e_val_s = N * p_val_s
        info_real.loc[i,'e_value'] = e_val_s
    return info_real[:][info_real['p_value'] < p_val_limit]


def log_pwm(pwm):
    pwm_log = []
    for l in range(0, len(pwm)):
        profile = np.zeros(len(pwm[l]))
        for a in range(0, len(pwm[l])):
            if pwm[l][a] != 0:
                profile[a] = math.log(pwm[l][a])
            else:
                print("PROBABILITIES ARE 0! log leads to NAN -> \n")
                profile[a] = np.nan
        pwm_log.append(profile)
    return pwm_log

# THE main ;)
'''
def main():
    parser = argparse.ArgumentParser ( description='Translates a PWM into an IUPAC identifier and prints it' )
    parser.add_argument ( metavar='PWM_FILE', dest='pwm_file', type=str,
                          help='file with the pwm' )
    parser.add_argument ( metavar='BG_FILE', dest='bg_file', type=str,
                          help='file with the background model' )
    parser.add_argument ( metavar='DB_FOLDER', dest='db_folder', type=str,
                          help='folder to search for database match' )
    parser.add_argument ( metavar='PWM_ORDER', dest='pwm_order', type=int,
                          help='order of the model represented in the pwm file' )
    parser.add_argument ( '--db_order', dest='db_order', type=int, default=4,
                          help='order of database models' )
    parser.add_argument ( '--read_order', dest='read_order', type=int, default=1,
                          help='order for comparison needs to be lower or equal db /pwm order' )
    parser.add_argument ( '--shuffle_times', dest='shuffle_times', type=int, default=10,
                          help='how often to shuffle the pwm for the bakcground distribution' )
    parser.add_argument ( '--p_val_limit', dest='p_val_limit', type=float, default=0.1,
                          help='report matches up to p_val_limit' )
    parser.add_argument ( '--quantile', dest='quantile_of_interest', type=float, default=0.1,
                          help='which top percent to use for the function estimation' )

    args = parser.parse_args ( )

    weight = 0.25
    min_overlap = 4

    selfies = []

    # 1. get real infos
    # read pwm and log them
    pwm = read_pwm ( args.pwm_file, args.pwm_order, args.read_order )
    pwm_log = log_pwm(pwm)
    pwm_bg = read_bg(args.bg_file, args.pwm_order, len(pwm))
    pwm_bg_log = log_pwm(pwm_bg)
    info_real = get_scores ( pwm, pwm_bg, pwm_log, pwm_bg_log, args.db_folder, args.db_order, args.read_order , weight, min_overlap)


    # extract selfmatch score:
    self_match = get_selfmatch(info_real, args.pwm.file)
    selfies[s] = self_match 

    # get reverseComplement of pwm if read_order == 0 and score_matches
    if args.read_order == 0 :
        pwm_rev = reverseComp(pwm)
        pwm_rev_log = reverseComp(pwm_rev)
        bg_rev = reverseComp(pwm_bg)
        bg_rev_log = reverseComp(bg_rev)
        info_rev = get_scores ( pwm_rev, bg_rev,pwm_rev_log, bg_rev_log, args.db_folder, args.db_order, args.read_order , weight, min_overlap)
        info_real = info_real.append ( info_rev, ignore_index=True )
        info_real = info_real.reset_index ( )

    # 2. get x-times shuffled info and concatenate to calculate p_and_e_value
    frames = [info_real]
    for x in range (0, args.shuffle_times ):
        pwm_shuff = shuffle_pwm ( pwm )
        pwm_shuff_log = log_pwm(pwm_shuff)
        info_fake = get_scores ( pwm_shuff, pwm_bg, pwm_shuff_log, pwm_bg_log, args.db_folder, args.db_order, args.read_order , weight, min_overlap)
        frames.append ( info_fake )

        if args.read_order == 0:
            pwm_shuff_rev = shuffle_pwm ( pwm_rev )
            pwm_shuff_rev_log = log_pwm( pwm_shuff_rev )
            info_fake = get_scores ( pwm_shuff_rev, bg_rev, pwm_shuff_rev_log, bg_rev_log, args.db_folder, args.db_order, args.read_order, weight , min_overlap)
            frames.append ( info_fake )

    # 3. concatenate all and calculate pvalues and evalues for the entries
    info_all = pd.concat ( frames )

    best_reals = calclate_p_and_e_value ( info_real, info_all, args.quantile_of_interest, args.p_val_limit )
    best_reals = best_reals.sort_values ( by='p_value', ascending=[1, ] )
    best_reals = best_reals.reset_index ( )

    if len( best_reals ) == 0:
        print ( 'no matches!' )
    else:
        #print ( '%s' % '\n '.join ( map ( str, best_reals[i] ) ) )
        for i in range(0,len(best_reals)):
            print( str(best_reals['Name'][i]) + ' ' + str(best_reals['p_value'][i]) + ' ' + str(best_reals['e_value'][i]) + ' ' + str(best_reals['score'][i]) + ' ' + str(best_reals['offset_p'][i]) + ' ' + str(best_reals['offset_q'][i]) + ' ' + str(best_reals['W'][i]) )

# if called as a script; calls the main method
if __name__ == '__main__':
    main ( )

'''

weight = 0.9
min_overlap = 4
#pwm_file='/home/kiesel/Desktop/BaMM_webserver/DB/ENCODE_ChIPseq/Results/wgEncodeUwTfbsHcpeCtcfStdAlnRep0_summits125/wgEncodeUwTfbsHcpeCtcfStdAlnRep0_summits125_motif_1.ihbcp'
#bg_file='/home/kiesel/Desktop/BaMM_webserver/DB/ENCODE_ChIPseq/Results/wgEncodeUwTfbsHcpeCtcfStdAlnRep0_summits125/wgEncodeUwTfbsHcpeCtcfStdAlnRep0_summits125.hbcp'

#db_folder='/home/kiesel/Desktop/MARVIN_BACKUP/Results'  # with extensions but missing background model files
db_folder='/home/kiesel/Desktop/TomTomTool/Results'    # without extensions

pwm_order=4
db_order=4
read_order=0
shuffle_times=10
p_val_limit=0.1
quantile_of_interest=0.1

selfies = pd.DataFrame()

for entry in glob.iglob ( os.path.join ( db_folder + '/**/*.ihbcp' )):
    bg_file = os.path.join(db_folder + '/' +  str.split( ntpath.basename(entry), "_")[0] + '_summits125/' + str.split( ntpath.basename(entry), "_")[0] + '_summits125.hbcp')

    # 1. get real infos
    # read pwm and log them
    pwm = read_pwm ( entry, pwm_order, read_order )
    pwm_log = log_pwm(pwm)
    pwm_bg = read_bg(bg_file, read_order, len(pwm))
    pwm_bg_log = log_pwm(pwm_bg)
    info_real = get_scores ( pwm, pwm_bg, pwm_log, pwm_bg_log, db_folder, db_order, read_order , weight, min_overlap)


    # extract selfmatch score:
    self_match = get_selfmatch(info_real, entry)
    selfies.append(self_match)

    # get reverseComplement of pwm if read_order == 0 and score_matches
    if read_order == 0 :
        pwm_rev = reverseComp(pwm)
        pwm_rev_log = reverseComp(pwm_rev)
        #bg_rev = reverseComp(pwm_bg)
        #bg_rev_log = reverseComp(bg_rev)
        #info_rev = get_scores ( pwm_rev, bg_rev,pwm_rev_log, bg_rev_log, db_folder, db_order, read_order , weight, min_overlap)
        info_rev = get_scores ( pwm_rev, pwm_bg,pwm_rev_log, pwm_bg_log, db_folder, db_order, read_order , weight, min_overlap)
        info_real = info_real.append ( info_rev, ignore_index=True )
        info_real = info_real.reset_index ( )

    # 2. get x-times shuffled info and concatenate to calculate p_and_e_value
    info_all = pd.DataFrame()
    info_all = info_all.append(info_real)
    for x in range (0, shuffle_times ):
        pwm_shuff = shuffle_pwm ( pwm )
        pwm_shuff_log = log_pwm(pwm_shuff)
        info_fake = get_scores ( pwm_shuff, pwm_bg, pwm_shuff_log, pwm_bg_log, db_folder, db_order, read_order , weight, min_overlap)
        info_all = info_all.append ( info_fake )

        if read_order == 0:
            pwm_shuff_rev = shuffle_pwm ( pwm_rev )
            pwm_shuff_rev_log = log_pwm( pwm_shuff_rev )
            info_fake = get_scores ( pwm_shuff_rev, bg_rev, pwm_shuff_rev_log, bg_rev_log, db_folder, db_order, read_order, weight , min_overlap)
            info_all = info_all.append ( info_fake )

    # 3. calculate p_values
    best_reals = calclate_p_and_e_value ( info_real, info_all, args.quantile_of_interest, args.p_val_limit )
    best_reals = best_reals.sort_values ( by='p_value', ascending=[1, ] )
    best_reals = best_reals.reset_index ( )

    if len( best_reals ) == 0:
        print ( 'no matches!' )
    else:
        #print ( '%s' % '\n '.join ( map ( str, best_reals[i] ) ) )
        for i in range(0,len(best_reals)):
            print( str(best_reals['Name'][i]) + ' ' + str(best_reals['p_value'][i]) + ' ' + str(best_reals['e_value'][i]) + ' ' + str(best_reals['score'][i]) + ' ' + str(best_reals['offset_p'][i]) + ' ' + str(best_reals['offset_q'][i]) + ' ' + str(best_reals['W'][i]) )



for x in range (0, shuffle_times ):
    print("random #:" + str(x))
    pwm_shuff = shuffle_pwm ( pwm )
    pwm_shuff_log = log_pwm(pwm_shuff)
    info_fake = get_scores ( pwm_shuff, pwm_bg, pwm_shuff_log, pwm_bg_log, db_folder, db_order, read_order , weight, min_overlap)
    frames = frames.append ( info_fake )
    if read_order == 0:
        print(" reverse ...\n")
        pwm_shuff_rev = shuffle_pwm ( pwm_rev )
        pwm_shuff_rev_log = log_pwm( pwm_shuff_rev )
        info_fake = get_scores ( pwm_shuff_rev, bg_rev, pwm_shuff_rev_log, bg_rev_log, db_folder, db_order, read_order, weight , min_overlap)
        frames = frames.append ( info_fake )
