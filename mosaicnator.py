#!/data2/external_data/Abyzov_Alexej_m124423/apps/pyenv/versions/3.5.1/bin/python

import argparse
from worker import (
    Somatic,
    Sensitivity,
    Pairwise)

def somatic(args):
        s = Somatic(args)
        s.run()

def sensitivity(args):
    s = Sensitivity(args)
    s.run()

def pairwise(args):
    s = Pairwise(args)
    s.run()

def main():
    parser = argparse.ArgumentParser(
        description='Somatic Mosaic SNV/indel caller')
    subparsers = parser.add_subparsers(help='commands')

    # =================================
    # Common arguments for all commands
    # =================================
    parser_common = argparse.ArgumentParser(add_help=False)

    parser_common.add_argument(
        '-f', '--min-AF', metavar='FLOAT',
        help='AF cutoff value [0.35]',
        type=float, default=0.35)

    parser_common.add_argument(
        '-q', '--min-MQ', metavar='INT',
        help='mapQ cutoff value for AF calculation [20]',
        type=int, default=20)

    parser_common.add_argument(
        '-Q', '--min-BQ', metavar='INT',
        help='baseQ/BAQ cutoff value for AF calculation [13]',
        type=int, default=13)

    parser_common.add_argument(
        '-n', '--no-skip', dest='skip_on', action='store_false',
        help='Do not skip. Rerun from the scratch. [off]',
        default=True)

    parser_common.add_argument(
        '-e', '--exome', dest='chunk_on', action='store_false',
        help='Do not use chunk as it uses WES data. [off]',
        default=True)

    parser_common.add_argument(
        '-r', '--ref', metavar='FILE',
        help='refence sequence file',
        required=True)

    parser_common.add_argument(
        '-v', '--var', metavar='', dest='var_type',
        help='Variant type for calling. [snv]',
        choices=['snv', 'indel'], default='snv')

    parser_common.add_argument(
        'infile', metavar='sample_list.txt',
        help='''Matched sample list file. 
        Each line format is 
        "clone.bam\\ttissue.bam" or 
        "tumor.bam\\tnormal.bam". 
        Each column should have full path for bam file.
        Trailing columns will be ignored. 
        For 'sensitivity' or 'pairwise' command,  
        only the first column will be used.''')

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
        '-b', '--control-bam', metavar='FILE',
        help='na12878 bam file',
        required=True)

    parser_sensitivity.add_argument(
        '-c', '--control-var', metavar='FILE',
        help='''na12878 SNP or INDEL list. 
        Each line format is "chr\\tpos\\tref\\talt".
        Trailing columns will be ignored.''',
        required=True)

    parser_sensitivity.add_argument(
        '-k', '--g1k-var', metavar='FILE',
        help='''1KG SNP or INDEL list.
        Each line format is "chr\\tpos\\tref\\talt".
        Trailing columns will be ignored.''',
        required=True)

    parser_sensitivity.add_argument(
        '-g', '--germ-het-var', metavar='FILE',
        help='''Germline hetero SNP or INDEL list.
        Each line format is "chr\\tpos\\tref\\talt".
        Trailing columns will be ignored.''',
        required=True)

    parser_sensitivity.set_defaults(func=sensitivity)

    # ========================== 
    # pairwise command arguments
    # ==========================
    
    parser_pairwise = subparsers.add_parser(
        'pairwise', parents=[parser_common],
            help='''All pairwise comparison for clones''')

    parser_pairwise.add_argument(
        '-o', '--out-prefix', metavar='STR',
        help='''Prefix string for out file. ['']''',
        type=str, default='')
    
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
