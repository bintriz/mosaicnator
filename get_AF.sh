#!/bin/bash
#$ -N get_AF
#$ -q 1-day
#$ -cwd
#$ -o q.out
#$ -e q.err
##$ -M bae.taejeong@mayo.edu
##$ -m abe
#$ -l h_vmem=12G

. /home/m130621/.bash_profile > /dev/null
plenv shell 5.22.0

ref=$1
clone=$2
tissue=$3
snp=$4
out=$5

echo "Start:" $(date +"%F %T")
./get_AF.pl -r $ref -c $clone -t $tissue -s $snp > $out
echo "End:" $(date +"%F %T")
