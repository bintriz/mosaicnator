#!/bin/bash
#$ -cwd

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
CHUNKFILE=$5
THREADS=$6

INTERVAL=$(awk "NR==${SGE_TASK_ID}" $CHUNKFILE)
OUTDIR=$OUTPREFIX.${INTERVAL/:/-}
OUTFILE=$OUTDIR/somatic.5x.indel.vcf.gz
VCFFILE=$OUTDIR/somatic.5x.indel.vcf
CHECKSUMDIR=$OUTDIR/checksum
OUTMD5=$CHECKSUMDIR/$(basename $OUTFILE).md5

if [ -f $OUTFILE ] && [ -f $OUTMD5 ] && \
       [ "$(md5sum $OUTFILE|cut -f1 -d' ')" = "$(cut -f1 -d' ' $OUTMD5)" ]; then
    echo "$OUTFILE exist and match to the corresponding checksum."
    exit 0
else
    rm -rf $OUTDIR
fi

scalpel --somatic --tumor $CLONEBAM --normal $TISSUEBAM --bed $INTERVAL --dir $OUTDIR \
	--ref $REF --numproc $THREADS --two-pass --window 600

if [ -f $VCFFILE ]; then
    bgzip -c $VCFFILE > $OUTFILE
else
    bgzip -c $OUTDIR/main/somatic.5x.indel.vcf > $OUTFILE
fi

mkdir -p $CHECKSUMDIR
md5sum $OUTFILE > $OUTMD5
