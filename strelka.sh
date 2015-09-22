#!/bin/bash
#$ -N strelka
#$ -q 1-day
#$ -cwd
#$ -o q.out
#$ -e q.err
#$ -pe threaded 16
##$ -M bae.taejeong@mayo.edu
##$ -m abe

. ~/.bash_profile > /dev/null

ref=$1
tumor=$2
normal=$3
outdir=$4
strelka_home=~/apps/strelka/current

echo "Start" $(date +"%F %T")
configureStrelkaWorkflow.pl --ref $ref --tumor $tumor --normal $normal \
	--config $strelka_home/etc/strelka_config_bwa_default.ini --output-dir $outdir
make -j 16 -C $outdir
echo "End:" $(date +"%F %T")
