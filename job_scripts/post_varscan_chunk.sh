#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=16G

. ~/.bash_profile > /dev/null

refidx=$1
chunksize=$2
datadir=$3
sample=$4

# =============
# varscan merge
# =============

snpout=$datadir/$sample.varscan.snp
head -n1 $(ls $datadir/*.varscan.*.snp|head -n1) > $snpout
indelout=$datadir/$sample.varscan.indel
head -n1 $(ls $datadir/*.varscan.*.indel|head -n1) > $indelout

for i in $(cat $refidx|cut -f-2|sed 's/\t/:/'); do
    chrom=${i/:*/}
    chromsize=${i/*:/}
    for start in $(seq 1 $chunksize $chromsize); do
	end=$(($start + $chunksize - 1))
	if [ $end -gt $chromsize ]; then
	    end=$chromsize
	fi
	snpchunk=$datadir/$sample.varscan.$chrom-$start-$end.snp
	tail -n+2 $snpchunk >> $snpout
	rm $snpchunk
	
	indelchunk=$datadir/$sample.varscan.$chrom-$start-$end.indel
	tail -n+2 $indelchunk >> $indelout
	rm $indelchunk
    done
done

# ======================
# varscan processSomatic
# ======================

varscan processSomatic $snpout --p-value 0.05
varscan processSomatic $indelout --p-value 0.05
