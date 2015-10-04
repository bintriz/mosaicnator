#!/bin/bash

######## aggregate snp_coord by call_n
samples=$(ls data.snp_coord|cut -d. -f1|sort|uniq)
for sample in $samples; do
    echo aggregate $sample snp_coord by call_n
    for n in 1 2 3 4; do
        cat data.snp_coord/$sample.{mutect,somaticsniper,strelka,varscan}.snp_coord.txt|sort|uniq -c \
	    |grep -P "^\s+$n"|sed -e "s/^\s\+$n\s//" > data.snp_coord/$sample.call_n$n.snp_coord.txt
    done
done
