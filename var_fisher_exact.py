#!/data2/external_data/Abyzov_Alexej_m124423/apps/pyenv/versions/3.5.1/bin/python

import argparse
import re
import scipy.stats as stats
import subprocess
import sys
import os


config = os.path.dirname(os.path.realpath(__file__)) + "/job.config"
with open(config) as f:
    for line in f:
        if line[:9] == "SAMTOOLS=":
            exec(line)
            break

def print_stat(args):
    stat_test = fisher_exact(
        ref_alt_n(pileup(args.case, args.min_MQ, args.min_BQ, clean(count()))),
        ref_alt_n(pileup(args.control, args.min_MQ, args.min_BQ, clean(count()))))
    sample_info = '##case   : {}\n##control: {}\n'.format(
        ', '.join(os.path.basename(bam) for bam in args.case), 
        ', '.join(os.path.basename(bam) for bam in args.control))
    header = (sample_info + '#chr\tpos\tref\talt\tpvalue\t' +
              'case_ref_n\tcase_alt_n\tcontrol_ref_n\tcontrol_alt_n')
    printer(header)
    for snv in args.infile:
        if snv[0] == '#':
            continue
        chrom, pos, ref, alt = snv.strip().split()[:4]
        result = stat_test.send((chrom, pos, ref, alt))
        printer('{}\t{}\t{}\t{}\t{}'.format(chrom, pos, ref, alt, result))
            
def coroutine(func):
    def start(*args, **kwargs):
        g = func(*args, **kwargs)
        g.__next__()
        return g
    return start

@coroutine
def fisher_exact(target_c, target_t):
    result = None
    while True:
        chrom, pos, ref, alt = (yield result)
        ref_n_c, alt_n_c = target_c.send((chrom, pos, ref, alt))
        ref_n_t, alt_n_t = target_t.send((chrom, pos, ref, alt))
        oddsratio, pvalue = stats.fisher_exact([[ref_n_c, alt_n_c],[ref_n_t, alt_n_t]])
        result = '{:.5e}\t{}\t{}\t{}\t{}'.format(
            pvalue, ref_n_c, alt_n_c, ref_n_t, alt_n_t)

@coroutine
def ref_alt_n(target):
    result = None
    while True:
        chrom, pos, ref, alt = (yield result)
        base_n = target.send((chrom, pos))
        ref_n = base_n[ref.upper()] + base_n[ref.lower()]
        alt_n = base_n[alt.upper()] + base_n[alt.lower()]
        result = (ref_n, alt_n)

@coroutine
def pileup(bams, min_MQ, min_BQ, target):
    cmd = [SAMTOOLS, 'mpileup', '-d', '8000', '-q', str(min_MQ), '-Q', str(min_BQ)]
    result = None
    while True:
        chrom, pos = (yield result)
        region = ['-r', '{}:{}-{}'.format(chrom, pos, pos)]
        bases = ''
        for bam in bams:
            try:
                bases = bases + subprocess.run(
                    cmd + region + [bam], universal_newlines=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL).stdout.split()[4]
            except IndexError:
                pass
        result = target.send(bases)

@coroutine
def clean(target):
    result = None
    while True:
        bases = (yield result)
        bases = re.sub('\^.', '', bases)
        bases = re.sub('\$', '', bases)
        for n in set(re.findall('-(\d+)', bases)):
            bases = re.sub('-{0}[ACGTNacgtn]{{{0}}}'.format(n), '', bases)
        for n in set(re.findall('\+(\d+)', bases)):
            bases = re.sub('\+{0}[ACGTNacgtn]{{{0}}}'.format(n), '', bases)
        result = target.send(bases)

@coroutine
def count():
    result = None
    while True:
        bases = (yield result)
        base_n = {}
        base_n['A'] = bases.count('A') 
        base_n['C'] = bases.count('C')
        base_n['G'] = bases.count('G')
        base_n['T'] = bases.count('T')
        base_n['a'] = bases.count('a')
        base_n['c'] = bases.count('c')
        base_n['g'] = bases.count('g')
        base_n['t'] = bases.count('t')
        base_n['dels'] = bases.count('*')
        result = base_n

def printer(out):
    try:
        print(out, flush=True)
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        try:
            sys.stderr.close()
        except BrokenPipeError:
            pass
        
def main():
    parser = argparse.ArgumentParser(
        description='Calculate allele freqeuency for SNV')

    parser.add_argument(
        '-c', '--case', metavar='FILE',
        help='case bam file', 
        required=True, action='append')

    parser.add_argument(
        '-t', '--control', metavar='FILE',
        help='control bam file',
        required=True, action='append')

    parser.add_argument(
        '-q', '--min-MQ', metavar='INT',
        help='mapQ cutoff value [20]',
        type=int, default=20)

    parser.add_argument(
        '-Q', '--min-BQ', metavar='INT',
        help='baseQ/BAQ cutoff value [13]',
        type=int, default=13)
    
    parser.add_argument(
        'infile', metavar='snv_list.txt',
        help='''SNV list.
        Each line format is "chr\\tpos\\t\\tref\\alt".
        Trailing columns will be ignored. [STDIN]''',
        nargs='?', type=argparse.FileType('r'),
        default=sys.stdin)

    parser.set_defaults(func=print_stat)
    
    args = parser.parse_args()

    if(len(vars(args)) == 0):
        parser.print_help()
    else:
        args.func(args)
        
if __name__ == "__main__":
    main()
