#!/bin/bash
#$ -q 4-days
#$ -cwd

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
CHECKSUMDIR=$(dirname $OUTPREFIX)/checksum
MD5PREFIX=$CHECKSUMDIR/$(basename $OUTPREFIX)

if [ -f $OUTPREFIX.vcf ] && [ -f $MD5PREFIX.vcf.md5 ] && \
       [ "$(md5sum $OUTPREFIX.vcf|cut -f1 -d' ')" = "$(cut -f1 -d' ' $MD5PREFIX.vcf.md5)" ]; then
    echo "$OUTPREFIX.vcf exists and matches to the corresponding checksum."
    exit 0
else
    rm -rf $OUTPREFIX.vcf $MD5PREFIX.vcf.md5
fi

bam-somaticsniper -q 5 -Q 20 -s 0.000001 -F vcf -f $REF $CLONEBAM $TISSUEBAM $OUTPREFIX.vcf

mkdir -p $CHECKSUMDIR
md5sum $OUTPREFIX.vcf > $MD5PREFIX.vcf.md5
