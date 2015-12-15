#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

datadir=$1
sample=$2

# ============================
# somaticsniper filter out LOH
# ============================

vcf=$datadir/$sample.somaticsniper.vcf
outfile=$datadir/$sample.somaticsniper.somatic.vcf
grep ^# $vcf > $outfile
grep -v ^# $vcf|perl -ne 'if(/:2:\d+\n/) {print}' >> $outfile
