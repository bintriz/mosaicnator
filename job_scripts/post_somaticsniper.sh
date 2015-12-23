#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

PREFIX=$1
VCF=$PREFIX.vcf
VCFMD5=$(dirname $PREFIX)/checksum/$(basename $PREFIX).vcf.md5
OUTFILE=$PREFIX.somatic.vcf
OUTMD5=$(dirname $PREFIX)/checksum/$(basename $PREFIX).somatic.vcf.md5

if [ ! -f $VCF ] || [ ! -f $VCFMD5 ] || \
       [ "$(md5sum $VCF)" != "$(cat $MD5PREFIX.vcf.md5)" ]; then
    echo "$VCF doesn't exist or doesn't match to the ckesksum"
    exit 1
fi

# ============================
# somaticsniper filter out LOH
# ============================

grep ^# $VCF > $OUTFILE
grep -v ^# $VCF|perl -ne 'if(/:2:\d+\n/) {print}' >> $OUTFILE

# ===============
# Create checksum
# ===============

md5sum $OUTFILE > $OUTMD5
