#!/bin/bash
#$ -q 4-days
#$ -cwd

source $BIN_PATH/job.config

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
CHECKSUMDIR=$(dirname $OUTPREFIX)/checksum
MD5PREFIX=$CHECKSUMDIR/$(basename $OUTPREFIX)

if [[ -f $OUTPREFIX.vcf && -f $MD5PREFIX.vcf.md5 && \
        $(md5sum $OUTPREFIX.vcf|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $MD5PREFIX.vcf.md5) ]]; then
    echo "$OUTPREFIX.vcf exists and matches to the corresponding checksum."
else
    rm -f $OUTPREFIX.vcf $MD5PREFIX.vcf.md5
    $SOMATICSNIPER -q 5 -Q 20 -s 0.000001 -F vcf -f $REF \
        $CLONEBAM $TISSUEBAM $OUTPREFIX.vcf
    if [[ $? = 0 ]]; then
        mkdir -p $CHECKSUMDIR
        md5sum $OUTPREFIX.vcf > $MD5PREFIX.vcf.md5
    fi
fi
