#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

sample=$1
datadir=$2
outdir=$3

for i in 1 2 3 4; do
    concall=$datadir/$sample.call_n$i.snv_AF.txt
    printf "#chr\tpos\tref\talt\tsnv_AF\n" > $concall
    tail -qn+2 $datadir/$sample.{mutect,somaticsniper,strelka,varscan}.snv_AF.txt \
	|cut -f-5 \
	|q -t "SELECT c1, c2, c3, c4, c5, count(*) FROM - GROUP BY c1, c2, c3, c4, c5" \
	|awk -v call_n=$i '$6 == call_n' \
	|cut -f-5 >> $concall
done

call_n4=$datadir/$sample.call_n4.snv_AF.txt
cutoff=$outdir/$sample.snv_call_n4_${af/0./}AFcutoff.txt
printf "#chr\tpos\tref\talt\tsnv_AF\n" > $cutoff
tail -n+2 $call_n4 \
    |awk -v af=$af '$5 >= af' >> $cutoff
