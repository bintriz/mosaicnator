#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=16G

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
INTERVAL=$5

echo "Start:" $(date +"%F %T")
samtools mpileup -f $REF -r $INTERVAL $TISSUEBAM $CLONEBAM|varscan 8 somatic --mpileup $OUTPREFIX
echo "End:" $(date +"%F %T")
