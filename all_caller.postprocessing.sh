#!/bin/bash

[ $# -lt 2 ] && { echo -e "Usage:\n  $(basename "$0") sample.name data.dir"; exit 1; }

sample=$1
datadir=$2

##
## somaticsniper filter out LOH
##
vcf=$datadir/$sample.somaticsniper.vcf
outfile=$datadir/$sample.somaticsniper.somatic.vcf
grep ^# $vcf > $outfile
grep -v ^# $vcf|perl -ne 'if(/:2:\d+\n/) {print}' >> $outfile

##
## mutect filter KEEP & merge
##
subdir=$datadir/$sample.mutect
outfile=$datadir/$sample.mutect.txt
head -n2 $(ls $subdir/*.mutect.*.txt|head -n1) > $outfile
for subfile in $(ls $subdir/*.mutect.*.txt); do
    tail -n+3 $subfile |grep KEEP$ >> $outfile
    rm $subfile
done
rmdir $subdir

##
## varscan merge $ run processSomatic
##
subdir=$datadir/$sample.varscan
outfile=$subdir/$sample.varscan.snp
head -n1 $(ls $subdir/*.varscan.*.snp|head -n1) > $outfile
for subfile in $(ls $subdir/*.varscan.*.snp); do
    tail -n+2 $subfile >> $outfile
    rm $subfile
done
varscan processSomatic $outfile --p-value 0.05

outfile=$subdir/$sample.varscan.indel
head -n1 $(ls $subdir/*.varscan.*.indel|head -n1) > $outfile
for subfile in $(ls $subdir/*.varscan.*.indel); do
    tail -n+2 $subfile >> $outfile
    rm $subfile
done
varscan processSomatic $outfile --p-value 0.05
