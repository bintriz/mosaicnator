#!/data2/external_data/Abyzov_Alexej_m124423/apps/pyenv/versions/3.5.0/bin/python

import argparse
from worker import (
    SomaticCall,
    PostProcess,
    AlleleFreq)
from utils import (
    read_sample_pairs,
    read_samples)


def somatic_call(args):
    ref = args.ref
    out_dir = 'data.somatic_call'
    
    c = SomaticCall(ref, out_dir)
    for clone, tissue in read_sample_pairs(args.infile):
        c.run(clone, tissue)
    #c.wait()

def somatic_af(args):
    ref = args.ref
    data_dir = 'data.somatic_call'
    out_dir = 'data.AF'

    print(ref)
    # p = PostProcess(ref, data_dir)
    # for sample in read_samples(args.infile):
    #     p.run(sample)
    # p.wait()
    
    # f = AlleleFreq(ref, data_dir, out_dir)
    # for clone, tissue in read_sample_pairs(args.infile):
    #     f.run(clone, tissue)
    # f.wait()
        
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
        help='''Matched sample list file. 
        Each line format is 
        "clone.bam<tab>tissue.bam" or 
        "tumor.bam<tab>normal.bam". 
        Each column should have full path for bam file.
        Trailing columns are ignored.''')
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

    # ============================
    # somatic_af command arguments
    # ============================
    
    parser_somatic_af = subparsers.add_parser(
        'somatic_af',
         help='Calculate allele frequency for somatic calls')
    parser_somatic_af.add_argument(
        'infile',
        metavar='sample_list.txt',
        help='''Matched sample list file. 
        Each line format is 
        "clone.bam<tab>tissue.bam" or 
        "tumor.bam<tab>normal.bam". 
        Each column should have full path for bam file.
        Trailing columns are ignored.''')
    parser_somatic_af.add_argument(
        '--ref',
        metavar='ref.fasta',
        help='refence.fasta file',
        required=True)
    parser_somatic_af.add_argument(
        '--type',
        choices=['snv', 'indel', 'all'],
        help='variant type')
    parser_somatic_af.set_defaults(func=somatic_af)
    
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

    if(len(vars(args)) == 0):
        parser.print_help()
    else:
        args.func(args)

if __name__ == "__main__":
    main()
