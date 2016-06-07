#!/bin/bash
#$ -cwd

source $BIN_PATH/job.config

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
CHUNKFILE=$5
THREADS=$6

INTERVAL=$(awk "NR==${SGE_TASK_ID}" $CHUNKFILE)
OUTDIR=$OUTPREFIX.${INTERVAL/:/-}
OUT=$OUTDIR/somatic.5x.indel.vcf.gz
VCF=$OUTDIR/somatic.5x.indel.vcf
CHECKSUMDIR=$OUTDIR/checksum
OUTMD5=$CHECKSUMDIR/$(basename $OUT).md5

if [[ -f $OUT && -f $OUTMD5 && \
        $(md5sum $OUT|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $OUTMD5) ]]; then
    echo "$OUT exist and match to the corresponding checksum."
else
    rm -rf $OUTDIR
    $SCALPEL --somatic --tumor $CLONEBAM --normal $TISSUEBAM --bed $INTERVAL --dir $OUTDIR \
        --ref $REF --numproc $THREADS --two-pass --window 600
    if [[ $? = 0 ]]; then
        if [[ -f $VCF ]]; then
            bgzip -c $VCF > $OUT
        else
            bgzip -c $OUTDIR/main/somatic.5x.indel.vcf > $OUT
        fi
        mkdir -p $CHECKSUMDIR
        md5sum $OUT > $OUTMD5
    fi
fi
