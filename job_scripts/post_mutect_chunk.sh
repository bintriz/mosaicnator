#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

REFIDX=$1
CHUNKSIZE=$2
DATADIR=$3
SAMPLE=$4

# ==========================
# mutect filter KEEP & merge
# ==========================

OUTFILE=$DATADIR/$SAMPLE.mutect.keep.txt
head -n2 $(ls $DATADIR/*.mutect.*.txt|head -n1) > $OUTFILE
for i in $(cat $REFIDX|cut -f-2|sed 's/\t/:/'); do
    CHROM=${i/:*/}
    CHROMSIZE=${i/*:/}
    for START in $(seq 1 $CHUNKSIZE $CHROMSIZE); do
	END=$(($START + $CHUNKSIZE - 1))
	if [ $END -gt $CHROMSIZE ]; then
	    END=$CHROMSIZE
	fi
	CHUNKFILE=$DATADIR/$SAMPLE.mutect.$CHROM-$START-$END.txt
	tail -n+3 $CHUNKFILE |grep KEEP$ >> $OUTFILE
	rm $CHUNKFILE
    done
done
