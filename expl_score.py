#!/data2/external_data/Abyzov_Alexej_m124423/apps/pyenv/versions/3.5.1/bin/python

import argparse
import sys
from os import path
from collections import defaultdict
from math import sqrt

from pandas import Series, DataFrame

def get_sample_pair(fname):
    pair_name = path.basename(fname).split('.')[0]
    (case, control) = pair_name.split('_-_')
    return case, control

def get_sample_set(flist):
    sample_set = set(get_sample_pair(fname)[0] for fname in flist)
    return sample_set

def get_variant_dict(flist):
    var_dict = defaultdict(list)
    for fname in flist:
        spair = get_sample_pair(fname)
        with open(fname) as f:
            next(f)
            for line in f:
                var = tuple(line.split()[:4])
                var_dict[var].append(spair)
    return var_dict
            
def get_call_df(call_list, sample_set):
    data = [Series(0, index=sample_set) for sample in sample_set]
    call_df = DataFrame(data, index=sample_set)
    for case, control in call_list:
        call_df.ix[case, control] = 1
    return call_df

def get_cell_freq(call_n, sample_n):
    cell_freq = 1/2 - sqrt(1/4 - call_n/sample_n**2)
    return cell_freq

def main():
    parser = argparse.ArgumentParser(
        description='Caculate explanation score')

    parser.add_argument(
        'infile', metavar='FILE',
        help='''Consensus call file list.
        ''',
        nargs='?', type=argparse.FileType('r'),
        default=sys.stdin)

    args = parser.parse_args()

    flist = [line.strip() for line in args.infile]
    sample_set = get_sample_set(flist)
    sample_n = len(sample_set)
    var_dict = get_variant_dict(flist)

    print("#chr\tpos\tref\talt\tcell_freq\texplanation_score")
    for variant, call_list in var_dict.items():
        call_n = len(call_list)
        cell_freq = get_cell_freq(call_n, sample_n)
        pos_sample_n = round(cell_freq*sample_n)
        
        call_df = get_call_df(call_list, sample_set)
        ordered_col_sum = call_df.sum(1).sort_values(ascending=False)
        explained_call_n = ordered_col_sum[:pos_sample_n].sum()
        explanation_score = explained_call_n / call_n
    
        print('%s\t%s\t%s\t%s\t' % variant, end='')
        print('%s\t%s' % (cell_freq, explanation_score))

if __name__ == "__main__":
    main()        
