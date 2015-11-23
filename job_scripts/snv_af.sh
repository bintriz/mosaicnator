#!/bin/bash
#$ -N snv_af
#$ -q 1-day
#$ -cwd
#$ -o q.out
#$ -e q.err
#$ -l h_vmem=12G

. ~/.bash_profile > /dev/null
plenv shell 5.22.0

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
SNVCOORDFILE=$4
OUTFILE=$5

echo "Start:" $(date +"%F %T")
get_AF.pl -r $REF -c $CLONEBAM -t $TISSUEBAM -s $SNVCOORDFILE > $OUTFILE
echo "End:" $(date +"%F %T")
