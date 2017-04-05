
from collections import defaultdict
from enum import IntEnum
import numpy as np
import sys
import argparse
import math
import glob
import os
import ntpath

def get_model_order( filename ):
    order = -1
    with open ( filename ) as fh:
        for line in fh:
            tokens = line.split()
            if len(tokens) == 0 :
                return (order)
            else:
                order = order + 1
    return order

# THE main ;)
def main():
    parser = argparse.ArgumentParser ( description='returns model Order of BaMM file' )
    parser.add_argument ( metavar='BaMM_FILE', dest='bamm_file', type=str,
                          help='file with a BaMM model' )
    args = parser.parse_args ( )

    order = get_model_order ( args.bamm_file )

    print ( str(order))


# if called as a script; calls the main method
if __name__ == '__main__':
    main ( )

#filename = "/home/kiesel/Desktop/BaMM_webserver/media/b7179891-04bb-4219-be5b-8100f64367b7/Input/wgEncodeHaibTfbsA549Ctcfsc5916Pcr1xDex100nm_tq6Zm4n.ihbcp"
