#!/bin/bash
#$ -N run_somaticsniper
#$ -q 4-days
#$ -cwd
#$ -o q.out
#$ -e q.err

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4

echo "Start:" $(date +"%F %T")
bam-somaticsniper -q 5 -Q 20 -s 0.000001 -F vcf -f $REF $CLONEBAM $TISSUEBAM $OUTPREFIX.vcf
echo "End:" $(date +"%F %T")
