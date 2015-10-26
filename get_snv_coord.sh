#!/bin/bash

[ $# -lt 3 ] && { echo -e "Usage:\n  $(basename "$0") sample data.dir out.dir"; exit 1; }

sample=$1
datadir=$2
outdir=$3

if [ ! -d $outdir ]; then
    mkdir -p $outdir
fi

##
## mutect
##
tail -n+3 $datadir/$sample.mutect.txt \
    |cut -f-2,4-5 \
    |perl -ne '
	my ($chr, $pos, $ref, $alt) = split /\t/;
	chomp($alt);
	grep { print "$chr\t$pos\t$ref\t$_\n" } split /,/, $alt;
    ' > $outdir/$sample.mutect.snv_coord.txt

##
## somaticsniper
##
grep -v '^#' $datadir/$sample.somaticsniper.somatic.vcf \
    |cut -f-2,4-5 \
    |perl -ne '
	my ($chr, $pos, $ref, $alt) = split /\t/;
	chomp($alt);
	grep { print "$chr\t$pos\t$ref\t$_\n" } split /,/, $alt;
    ' > $outdir/$sample.somaticsniper.snv_coord.txt

##
## strelka
##
grep -v '^#' $datadir/$sample.strelka/results/passed.somatic.snvs.vcf \
    |cut -f-2,4-5 \
    |perl -ne '
	my ($chr, $pos, $ref, $alt) = split /\t/;
	chomp($alt);
	grep { print "$chr\t$pos\t$ref\t$_\n" } split /,/, $alt;
    ' > $outdir/$sample.strelka.snv_coord.txt

##
## varscan
##
tail -n+2 $datadir/$sample.varscan/$sample.varscan.snp.Somatic.hc \
    |cut -f-4 \
    |perl -ne '
	my ($chr, $pos, $ref, $alt) = split /\t/;
	chomp($alt);
	grep { print "$chr\t$pos\t$ref\t$_\n" } split /,/, $alt;
    ' > $outdir/$sample.varscan.snv_coord.txt
