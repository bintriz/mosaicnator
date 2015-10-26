#!/bin/bash

[ $# -lt 3 ] && { echo -e "Usage:\n  $(basename "$0") sample data.dir out.dir"; exit 1; }

sample=$1
datadir=$2
outdir=$3

if [ ! -d $outdir ]; then
    mkdir -p $outdir
fi

out=$outdir/$sample.snv_call_n4_35AFcutoff.txt
printf "#chr\tpos\tref\talt\tsnv_AF\n" > $out
tail -qn+2 $datadir/$sample.{mutect,somaticsniper,strelka,varscan}.snv_AF.txt \
    |cut -f-5 \
    |q -t "SELECT c1, c2, c3, c4, c5, count(*) FROM - GROUP BY c1, c2, c3, c4, c5" \
    |awk '$5 >= 0.35 && $6 == 4' \
    |cut -f-5 >> $out
