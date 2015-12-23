#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -pe threaded 16

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
SNVS=$OUTPREFIX/results/passed.somatic.snvs.vcf
INDELS=$OUTPREFIX/results/passed.somatic.indels.vcf
SNVSMD5=$OUTPREFIX/results/checksum/passed.somatic.snvs.vcf.md5
INDELSMD5=$OUTPREFIX/results/checksum/passed.somatic.indels.vcf.md5

if [ -f $SNVS ] && [ -f $SNVSMD5 ] && \
       [ "$(md5sum $SNVS)" = "$(cat $SNVSMD5)" ] && \
       [ -f $INDELS ] && [ -f $INDELSMD5 ] && \
       [ "$(md5sum $INDELS)" = "$(cat $INDELSMD5)" ]; then
    echo "$OUTPREFIX/results/passed.somatic.*.vcf exist and match to the corresponding checksum."
    exit 0
else
    rm -rf $OUTPREFIX
fi

configureStrelkaWorkflow.pl --ref $REF --tumor $CLONEBAM --normal $TISSUEBAM \
	--config ~/apps/strelka/current/etc/strelka_config_bwa_default.ini --output-dir $OUTPREFIX
make -j 16 -C $OUTPREFIX
rm -rf $OUTPREFIX/chromosomes

mkdir -p $OUTPREFIX/results/checksum
md5sum $SNVS > $SNVSMD5
md5sum $INDELS > $INDELSMD5
