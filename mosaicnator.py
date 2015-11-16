#!/data2/external_data/Abyzov_Alexej_m124423/apps/pyenv/versions/3.5.0/bin/python

import argparse
from job_queue import Queue
from somatic_caller import Caller
from utils import parse_sample_list_file


def somatic_call(args):
    ref = args.ref
    sample_list = parse_sample_list_file(args.infile)
    out_dir = 'data.somatic_call'
    
    c = Caller(ref, out_dir)
    for clone, tissue in sample_list:
#        print(clone, tissue)
        c.run(clone, tissue)
        
#    Queue().wait('somatic_call')

def main():
    parser = argparse.ArgumentParser(
        description='Somatic Mosaic SNV/indel caller')
    subparsers = parser.add_subparsers(help='commands')

    # ==============================
    # somatic_call command arguments
    # ==============================
    
    parser_somatic_call = subparsers.add_parser(
        'somatic_call',
         help='Run somatic callers')
    parser_somatic_call.add_argument(
        'infile',
        metavar='sample_list.txt',
        help='''Sample list file. 
        Each line format is 
        "clone.bam<tab>tissue.bam" or 
        "tumor.bam<tab>normal.bam".''')
    parser_somatic_call.add_argument(
        '--ref',
        metavar='ref.fasta',
        help='refence.fasta file',
        required=True)
    parser_somatic_call.add_argument(
        '--type',
        choices=['snv', 'indel', 'all'],
        help='variant type')
    parser_somatic_call.set_defaults(func=somatic_call)

    # ==================================
    # sensitivity_call command arguments
    # ==================================

    parser_sensitivity_call = subparsers.add_parser(
        'sensitivity_call',
        help='''Somatic call using NA12878 bam 
        for sensitivity estimation''')
    parser_sensitivity_call.add_argument(
        'sample_list.txt',
        help='''Sample list file. 
        Each line format is 
        "clone.bam<tab>NA12878.bam".''')
    parser_sensitivity_call.add_argument(
        '--ref',
        metavar='ref.fasta',
        help='refence.fasta file',
        required=True)
    parser_sensitivity_call.add_argument(
        '--type',
        choices=['snv', 'indel', 'all'],
        help='variant type')

    # ===============
    # parse arguments
    # ===============
    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
