#!/bin/bash
#$ -N snv_coord_mutect
#$ -q 1-day
#$ -cwd
#$ -o q.out
#$ -e q.err
#$ -l h_vmem=2G

. ~/.bash_profile > /dev/null

DATAFILE=$1
OUTFILE=$2

tail -n+3 $DATAFILE \
    |cut -f-2,4-5 \
    |perl -ne '
	my ($chr, $pos, $ref, $alt) = split /\t/;
	chomp($alt);
	grep { print "$chr\t$pos\t$ref\t$_\n" } split /,/, $alt;
    ' > $OUTFILE
