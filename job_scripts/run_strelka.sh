#!/bin/bash
#$ -N run_strelka
#$ -q 1-day
#$ -cwd
#$ -o q.out
#$ -e q.err
#$ -pe threaded 16

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4

echo "Start:" $(date +"%F %T")
configureStrelkaWorkflow.pl --ref $REF --tumor $CLONEBAM --normal $TISSUEBAM \
	--config ~/apps/strelka/current/etc/strelka_config_bwa_default.ini --output-dir $OUTPREFIX
make -j 16 -C $OUTPREFIX
echo "End:" $(date +"%F %T")
