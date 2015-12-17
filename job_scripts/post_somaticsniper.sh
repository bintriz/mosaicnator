#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

DATADIR=$1
SAMPLE=$2

# ============================
# somaticsniper filter out LOH
# ============================

VCF=$DATADIR/$SAMPLE.somaticsniper.vcf
OUTFILE=$DATADIR/$SAMPLE.somaticsniper.somatic.vcf
grep ^# $VCF > $OUTFILE
grep -v ^# $VCF|perl -ne 'if(/:2:\d+\n/) {print}' >> $OUTFILE
