#!/bin/bash
#$ -q 4-days
#$ -cwd
#$ -pe threaded 16
#$ -l h_vmem 8G

source $BIN_PATH/job.config

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTDIR=$4

THREADS=16
OUT=$OUTDIR/somatic.5x.indel.vcf.gz
CHECKSUMDIR=$OUTDIR/checksum
OUTMD5=$CHECKSUMDIR/$(basename $OUT).md5

if [[ -f $OUT && -f $OUTMD5 && \
        $(md5sum $OUT|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $OUTMD5) ]]; then
    echo "$OUT exist and match to the corresponding checksum."
else
    rm -rf $OUTDIR
    $SCALPEL --somatic --tumor $CLONEBAM --normal $TISSUEBAM --dir $OUTDIR \
        --ref $REF --numproc $THREADS --two-pass --window 600
    if [[ $? = 0 ]]; then
        bgzip -c ${OUT/%.gz} > $OUT
        mkdir -p $CHECKSUMDIR
        md5sum $OUT > $OUTMD5
    fi
fi
