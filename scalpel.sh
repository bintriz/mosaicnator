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

tumor=$1
normal=$2
interval=$4
out=$3.${interval/:/-}
numproc=$5

echo "Start:" $(date +"%F %T")
echo scalpel --somatic --tumor $tumor --normal $normal --bed $interval --dir $out \
	--ref data.ref/human_g1k_v37.fasta --numproc ${numproc:-10} --two-pass --window 600
echo "End:" $(date +"%F %T")
