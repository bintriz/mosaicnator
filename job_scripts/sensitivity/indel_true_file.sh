#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=8G
#$ -pe threaded 4

NA12878=$1
G1K=$2
GERM_HET=$3
OUT=$4
OUTMD5=$(dirname $OUT)/checksum/$(basename $OUT).md5

comm -12 <(sort -S2G $GERM_HET) <(sort -S20G $G1K) \
    |comm -23 - <(sort -S6G $NA12878) \
    |sort -k1,1V -k2,2n -S2G > $OUT

if [[ $? = 0 ]]; then
    mkdir -p $(dirname $OUTMD5)
    md5sum $OUT > $OUTMD5
fi
