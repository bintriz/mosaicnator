#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=8G
#$ -pe threaded 4

. ~/.bash_profile > /dev/null

NA12878=$1
G1K=$2
GERM_HET=$3
OUTFILE=$4
OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5

comm -12 <(sort -S2G $GERM_HET) <(sort -S20G $G1K) \
    |comm -23 - <(sort -S6G $NA12878) \
    |sort -k1,1V -k2,2n -S2G > $OUTFILE

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
