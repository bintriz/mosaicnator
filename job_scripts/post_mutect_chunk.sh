#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

refidx=$1
chunksize=$2
datadir=$3
sample=$4

# ==========================
# mutect filter KEEP & merge
# ==========================

outfile=$datadir/$sample.mutect.keep.txt
head -n2 $(ls $datadir/*.mutect.*.txt|head -n1) > $outfile
for i in $(cat $refidx|cut -f-2|sed 's/\t/:/'); do
    chrom=${i/:*/}
    chromsize=${i/*:/}
    for start in $(seq 1 $chunksize $chromsize); do
	end=$(($start + $chunksize - 1))
	if [ $end -gt $chromsize ]; then
	    end=$chromsize
	fi
	chunkfile=$datadir/$sample.mutect.$chrom-$start-$end.txt
	tail -n+3 $chunkfile |grep KEEP$ >> $outfile
	rm $chunkfile
    done
done
