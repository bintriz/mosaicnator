#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -pe threaded 16

source $BIN_PATH/job.config

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
SNVS=$OUTPREFIX/results/passed.somatic.snvs.vcf
INDELS=$OUTPREFIX/results/passed.somatic.indels.vcf
SNVSMD5=$OUTPREFIX/results/checksum/passed.somatic.snvs.vcf.md5
INDELSMD5=$OUTPREFIX/results/checksum/passed.somatic.indels.vcf.md5

if [[ -f $SNVS && -f $SNVSMD5 && \
        $(md5sum $SNVS|cut -f1 -d' ') = $(cut -f1 -d' ' $SNVSMD5) && \
        -f $INDELS && -f $INDELSMD5 && \
        $(md5sum $INDELS|cut -f1 -d' ') = $(cut -f -d' ' $INDELSMD5) ]]; then
    echo "$OUTPREFIX/results/passed.somatic.*.vcf exist and match to the corresponding checksum."
else
    rm -rf $OUTPREFIX
    $STRELKA --config $STRELKA_CONFIG --ref $REF \
        --tumor $CLONEBAM --normal $TISSUEBAM --output-dir $OUTPREFIX
    make -j 16 -C $OUTPREFIX
    if [[ $? = 0 ]]; then
        mkdir -p $OUTPREFIX/results/checksum
        md5sum $SNVS > $SNVSMD5
        md5sum $INDELS > $INDELSMD5
        rm -rf $OUTPREFIX/chromosomes
    fi
fi
