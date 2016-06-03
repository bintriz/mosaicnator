#!/bin/bash
#$ -q 1-day
#$ -cwd

PREFIX=$1
VCF=$PREFIX.vcf
VCFMD5=$(dirname $PREFIX)/checksum/$(basename $PREFIX).vcf.md5
OUT=$PREFIX.somatic.vcf
OUTMD5=$(dirname $PREFIX)/checksum/$(basename $PREFIX).somatic.vcf.md5

if [[ -f $VCF && -f $VCFMD5 && \
        $(md5sum $VCF|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $VCFMD5) ]]; then

    ## somaticsniper filter out LOH
    grep ^# $VCF > $OUT
    grep -v ^# $VCF|perl -ne 'if(/:2:\d+\n/) {print}' >> $OUT

    ## Create checksum
    if [[ $? = 0 ]]; then
        md5sum $OUT > $OUTMD5
    fi
else
    echo "$VCF doesn't exist or doesn't match to the ckesksum"
fi
