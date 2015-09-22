#!/bin/bash
#$ -N varscan
#$ -q 4-days
#$ -cwd
#$ -o q.out
#$ -e q.err
#$ -l h_vmem=16G
##$ -M bae.taejeong@mayo.edu
##$ -m abe

. ~/.bash_profile > /dev/null

ref=$1
tumor=$2
normal=$3
interval=$5

echo "Start:" $(date +"%F %T")
if [ "$interval" == "" ]; then
    out=$4
    samtools mpileup -f $ref $normal $tumor|varscan 8 somatic --mpileup $out
else
    out=$4.${interval/:/-}
    samtools mpileup -f $ref -r $interval $normal $tumor|varscan 8 somatic --mpileup $out
fi
echo "End:" $(date +"%F %T")
