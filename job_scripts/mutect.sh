#!/bin/bash
#$ -N mutect
#$ -q 4-days
#$ -cwd
#$ -o q.out
#$ -e q.err
##$ -M bae.taejeong@mayo.edu
##$ -m abe
#$ -l h_vmem=12G

. ~/.bash_profile > /dev/null

ref=$1
tumor=$2
normal=$3
out=$4
interval=$5

echo "Start:" $(date +"%F %T")
out=$out.${interval/:/-}
mutect 8 -I:tumor $tumor -I:normal $normal --out $out.txt --only_passing_calls -R $ref -L $interval
echo "End:" $(date +"%F %T")
