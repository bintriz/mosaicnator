#!/data2/external_data/Abyzov_Alexej_m124423/apps/pyenv/versions/3.5.1/bin/python


import argparse
import os
import subprocess
import sys
from tempfile import NamedTemporaryFile

def generic_parse(line):
    values = line.strip().split()
    chrom, pos, ref, alt = values[:4]
    info = "."
    return chrom, pos, ref, alt, info

def varscan_parse(line, header):
    values = line.strip().split()
    chrom, pos, ref, alt = values[:4]
    info = ';'.join(["%s=%s" % (key, val) for key, val in zip(header[4:],values[4:])])

    if(alt.startswith('+')):
        alt = alt.replace('+', ref)
    elif(alt.startswith('-')):
        alt = alt.replace('-', ref)
        ref, alt = alt, ref

    return chrom, pos, ref, alt, info

def vcf_header_generic():
    vcf_header = "##fileformat=VCFv4.2" + "\n" + \
                 "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
    return vcf_header

def vcf_header_varscan(header):
    info_header = "\n".join(["##INFO=<ID=%s,Number=1,Type=String,Description=\"VarScan output\">" % x for x in header[4:]])
    vcf_header = "##fileformat=VCFv4.2" + "\n" + \
                 info_header + "\n" + \
                 "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
    return vcf_header

def main():
    ##
    ## Build and parse options
    ##
    parser = argparse.ArgumentParser(description='VCF converter for VarScan output file')

    parser.add_argument('infile' , nargs='?',
                        type=argparse.FileType('rt'), default=sys.stdin,
                        help='''
                        Input variant file. 
                        It should include CHROM, POS, REF, and ALT as the first 4 columns for generic format. 
                        If this is ommited, default is STDIN.
                        ''')
    parser.add_argument('outfile', nargs='?',
                        type=argparse.FileType('wt'), default=sys.stdout,
                        help='''
                        Output vcf file.
                        If this is ommited, default is STDOUT.
                        ''')
    parser.add_argument('-d', '--seq-dict', required=True,
                        dest='seq_dict', action='store',
                        help='Sequence dictionary needed to sort vcf')
    parser.add_argument('-f', '--format', required=True,
                        dest='format', choices=['generic', 'varscan'],
                        help='''
                        Input file format. 
                        No header is assumed for generic format.
                        ''')

    try:
        args = parser.parse_args()
    except IOError as msg:
        parser.error(str(msg))

    ##
    ## Process options
    ##
    if(args.format == 'generic'):
        line_parse = generic_parse
        vcf_header = vcf_header_generic()
        
    elif(args.format == 'varscan'):
        header = args.infile.readline().strip().split()
        line_parse = lambda x: varscan_parse(x, header)
        vcf_header = vcf_header_varscan(header)

    ##
    ## Make Vcf
    ##
    with NamedTemporaryFile('wt', delete=False) as f_tmp:
        print(vcf_header, file=f_tmp)
        
        for line in args.infile:
            print("%s\t%s\t.\t%s\t%s\t.\t.\t%s" % line_parse(line), file=f_tmp)
            
    args.infile.close()

    ##
    ## Sort Vcf
    ##
    try:
        subprocess.check_call(["picard", "SortVcf", "CREATE_INDEX=false",
                               "I=" + f_tmp.name, "O=" + f_tmp.name + ".vcf", "SD=" + args.seq_dict])
    finally:
        os.remove(f_tmp.name)

    with open(f_tmp.name + ".vcf", 'rt') as f:
        for line in f:
            print(line.strip(), file=args.outfile)

    os.remove(f_tmp.name + ".vcf")
    args.outfile.close()

if __name__ == '__main__':
    main()
