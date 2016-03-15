#!/bin/bash
#$ -q 4-days
#$ -cwd
#$ -pe threaded 16
#$ -l h_vmem 8G

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTDIR=$4

THREADS=16
OUTFILE=$OUTDIR/somatic.5x.indel.vcf.gz
CHECKSUMDIR=$OUTDIR/checksum
OUTMD5=$CHECKSUMDIR/$(basename $OUTFILE).md5

if [ -f $OUTFILE ] && [ -f $OUTMD5 ] && \
       [ "$(md5sum $OUTFILE|cut -f1 -d' ')" = "$(cut -f1 -d' ' $OUTMD5)" ]; then
    echo "$OUTFILE exist and match to the corresponding checksum."
    exit 0
else
    rm -rf $OUTDIR
fi

scalpel --somatic --tumor $CLONEBAM --normal $TISSUEBAM --dir $OUTDIR \
	--ref $REF --numproc $THREADS --two-pass --window 600
bgzip -c ${OUTFILE/%.gz} > $OUTFILE

mkdir -p $CHECKSUMDIR
md5sum $OUTFILE > $OUTMD5
