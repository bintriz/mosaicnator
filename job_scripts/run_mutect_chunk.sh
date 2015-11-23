#!/bin/bash
#$ -N mutect
#$ -q 4-days
#$ -cwd
#$ -o q.out
#$ -e q.err
#$ -l h_vmem=12G

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
INTERVAL=$5

echo "Start:" $(date +"%F %T")
mutect 8 -I:tumor $CLONEBAM -I:normal $TISSUEBAM --out $OUTPREFIX.txt --only_passing_calls -R $REF -L $INTERVAL
echo "End:" $(date +"%F %T")
