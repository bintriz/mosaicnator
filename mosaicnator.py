#!/data2/external_data/Abyzov_Alexej_m124423/apps/pyenv/versions/3.5.0/bin/python

import argparse
from worker import (
    SomaticCall,
    PostProcess,
    SNVCoord,
    AlleleFreq,
    SNVConCall)
from utils import (
    read_sample_pairs,
    read_samples)


def somatic(args):
    ref = args.ref
    
    call = SomaticCall(ref, 'somatic.call')
    post = PostProcess(ref, 'somatic.call')
    coord = SNVCoord('somatic.call', 'somatic.AF')
    freq = AlleleFreq(ref, 'somatic.AF')
    con = SNVConCall('somatic.AF', 'somatic.out')

    for clone, tissue in read_sample_pairs(args.infile):
        hold_jid = call.run(clone, tissue)
        hold_jid = post.run(clone, tissue, hold_jid)
        hold_jid = coord.run(clone, tissue, hold_jid)
        hold_jid = freq.run(clone, tissue, hold_jid)
        con.run(clone, tissue, hold_jid)

def sensitivity(args):
    ref = args.ref
    tissue = args.bam

    call = SomaticCall(ref, 'sensitivity.call')
    post = PostProcess(ref, 'sensitivity.call')
    coord = SNVCoord('sensitivity.call', 'sensitivity.AF')
    freq = AlleleFreq(ref, 'sensitivity.AF')
    con = SNVConCall('sensitivity.AF', 'sensitivity.out')

    for clone in read_samples(args.infile):
        hold_jid = call.run(clone, tissue)
        hold_jid = post.run(clone, tissue, hold_jid)
        hold_jid = coord.run(clone, tissue, hold_jid)
        hold_jid = freq.run(clone, tissue, hold_jid)
        con.run(clone, tissue, hold_jid)

def pairwise(args):
    ref = args.ref
    
    call = SomaticCall(ref, 'pairwise.call')
    post = PostProcess(ref, 'pairwise.call')
    coord = SNVCoord('pairwise.call', 'pairwise.AF')
    freq = AlleleFreq(ref, 'pairwise.AF')
    con = SNVConCall('pairwise.AF', 'pairwise.out')

    for clone, tissue in read_samples(args.infile):
        hold_jid = call.run(clone, tissue)
        hold_jid = post.run(clone, tissue, hold_jid)
        hold_jid = coord.run(clone, tissue, hold_jid)
        hold_jid = freq.run(clone, tissue, hold_jid)
        con.run(clone, tissue, hold_jid)
        
def main():
    parser = argparse.ArgumentParser(
        description='Somatic Mosaic SNV/indel caller')
    subparsers = parser.add_subparsers(help='commands')

    # =========================
    # somatic command arguments
    # =========================
    
    parser_somatic = subparsers.add_parser(
        'somatic',
         help='Conventional somatic calling')

    parser_somatic.add_argument(
        'infile',
        metavar='sample_list.txt',
        help='''Matched sample list file. 
        Each line format is 
        "clone.bam<tab>tissue.bam" or 
        "tumor.bam<tab>normal.bam". 
        Each column should have full path for bam file.
        Trailing columns are ignored.''')

    parser_somatic.add_argument(
        '--ref',
        metavar='ref.fasta',
        help='refence.fasta file',
        required=True)

    parser_somatic.add_argument(
        '--type',
        choices=['snv', 'indel', 'all'],
        help='variant type')

    parser_somatic.set_defaults(func=somatic)
    
    # =============================
    # sensitivity command arguments
    # =============================

    parser_sensitivity = subparsers.add_parser(
        'sensitivity',
        help='''Sensitivity estimation using NA12878''')

    parser_sensitivity.add_argument(
        'infile',
        metavar='sample_list.txt',
        help='''Sample list file. 
        This command uses only first column(clone.bam).''')

    parser_sensitivity.add_argument(
        '--ref',
        metavar='ref.fasta',
        help='refence.fasta file',
        required=True)

    parser_sensitivity.add_argument(
        '--bam',
        metavar='na12878.bam',
        help='na12878.bam file',
        required=True)

    parser_sensitivity.add_argument(
        '--type',
        choices=['snv', 'indel', 'all'],
        help='variant type')
    parser_sensitivity.set_defaults(func=sensitivity)

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
