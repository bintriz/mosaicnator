#!/bin/bash
#$ -N somaticsniper
#$ -q 4-days
#$ -cwd
#$ -o q.out
#$ -e q.err
##$ -M bae.taejeong@mayo.edu
##$ -m abe

. ~/.bash_profile > /dev/null

ref=$1
tumor=$2
normal=$3
out=$4

echo "Start:" $(date +"%F %T")
bam-somaticsniper -q 5 -Q 20 -s 0.000001 -F vcf -f $ref $tumor $normal $out.vcf
echo "End:" $(date +"%F %T")
