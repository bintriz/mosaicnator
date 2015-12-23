#!/data2/external_data/Abyzov_Alexej_m124423/apps/pyenv/versions/3.5.0/bin/python

import argparse
from worker import (
    Somatic,
    Sensitivity,
    Pairwise)

def somatic(args):
    s = Somatic(args)
    s.run()
    s.end_msg()

def sensitivity(args):
    Sensitivity(args).run()

def pairwise(args):
    Pariwise(args).run()

def main():
    parser = argparse.ArgumentParser(
        description='Somatic Mosaic SNV/indel caller')
    subparsers = parser.add_subparsers(help='commands')

    # =================================
    # Common arguments for all commands
    # =================================
    parser_common = argparse.ArgumentParser(add_help=False)

    parser_common.add_argument(
        '--af', metavar='vaf',
        help='Variant allele frequency cutoff value (default: 0.35)',
        type=float, default=0.35)

    parser_common.add_argument(
        '--no-skip', dest='skip_on', action='store_false',
        help='''Do not skip. Rerun from the scratch. 
        (default: skip)''',
        default=True)

    parser_common.add_argument(
        '--exome', dest='chunk_on', action='store_false',
        help='''Do not use chunk as it uses WES data. 
        (default: WGS data using chunk)''',
        default=True)

    parser_common.add_argument(
        '--ref', metavar='ref.fasta',
        help='refence.fasta file',
        required=True)

    parser_common.add_argument(
        'infile', metavar='sample_list.txt',
        help='''Matched sample list file. 
        Each line format is 
        "clone.bam<tab>tissue.bam" or 
        "tumor.bam<tab>normal.bam". 
        Each column should have full path for bam file.
        Trailing columns are ignored. 
        'sensitivity' or 'pairwise' command uses 
        only the first column''')

    # =========================
    # somatic command arguments
    # =========================
    
    parser_somatic = subparsers.add_parser(
        'somatic', parents=[parser_common],
         help='Conventional somatic calling')

    parser_somatic.set_defaults(func=somatic)
    
    # =============================
    # sensitivity command arguments
    # =============================

    parser_sensitivity = subparsers.add_parser(
        'sensitivity', parents=[parser_common],
        help='''Sensitivity estimation using NA12878''')

    parser_sensitivity.add_argument(
        '--bam',
        metavar='na12878.bam',
        help='na12878.bam file',
        required=True)

    parser_sensitivity.set_defaults(func=sensitivity)

    # ========================== 
    # pairwise command arguments
    # ==========================
    
    parser_pairwise = subparsers.add_parser(
        'pairwise', parents=[parser_common],
            help='''All pairwise comparison for clones''')

    parser_pairwise.set_defaults(func=pairwise)

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
