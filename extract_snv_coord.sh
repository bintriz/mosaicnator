#!/bin/bash

[ $# -lt 2 ] && { echo -e "Usage:\n  $(basename "$0") data.dir out.dir"; exit 1; }

datadir=$1
outdir=$2
samples=$(ls $datadir|cut -f1 -d.|sort|uniq)

if [ ! -d $outdir ]; then
    mkdir -p $outdir
fi

for sample in $samples; do
    ######## mutect
    tail -n+3 $datadir/$sample.mutect.txt |cut -f-2,4-5 > $outdir/$sample.mutect.snv_coord.txt

    ######## somaticsniper
    grep -v '^#' $datadir/$sample.somaticsniper.somatic.vcf |cut -f-2,4-5 > $outdir/$sample.somaticsniper.snv_coord.txt

    ######## strelka
    grep -v '^#' $datadir/$sample.strelka/results/passed.somatic.snvs.vcf |cut -f-2,4-5 > $outdir/$sample.strelka.snv_coord.txt

    ######## varscan
    tail -n+2 $datadir/$sample.varscan/$sample.varscan.snp.Somatic.hc |cut -f-4 > $outdir/$sample.varscan.snv_coord.txt
done
