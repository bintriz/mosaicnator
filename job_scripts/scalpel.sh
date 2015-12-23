#!/bin/bash
#$ -N scalpel
#$ -q 1-day
#$ -cwd
#$ -o q.out
#$ -e q.err
##$ -M bae.taejeong@mayo.edu
##$ -m abe
#$ -l h_vmem=4G
#$ -pe threaded 10

. ~/.bash_profile > /dev/null

ref=$1
tumor=$2
normal=$3
interval=$5
out=$4.${interval/:/-}
numproc=$6

echo "Start:" $(date +"%F %T")
scalpel --somatic --tumor $tumor --normal $normal --bed $interval --dir $out \
	--ref $ref --numproc ${numproc:-10} --two-pass --window 600
echo "End:" $(date +"%F %T")
