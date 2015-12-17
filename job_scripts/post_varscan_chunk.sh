#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=16G

. ~/.bash_profile > /dev/null

REFIDX=$1
CHUNKSIZE=$2
DATADIR=$3
SAMPLE=$4

# =============
# varscan merge
# =============

SNPOUT=$DATADIR/$SAMPLE.varscan.snp
head -n1 $(ls $DATADIR/*.varscan.*.snp|head -n1) > $SNPOUT
INDELOUT=$DATADIR/$SAMPLE.varscan.indel
head -n1 $(ls $DATADIR/*.varscan.*.indel|head -n1) > $INDELOUT

for i in $(cat $REFIDX|cut -f-2|sed 's/\t/:/'); do
    CHROM=${i/:*/}
    CHROMSIZE=${i/*:/}
    for START in $(seq 1 $CHUNKSIZE $CHROMSIZE); do
	END=$(($START + $CHUNKSIZE - 1))
	if [ $END -gt $CHROMSIZE ]; then
	    END=$CHROMSIZE
	fi
	SNPCHUNK=$DATADIR/$SAMPLE.varscan.$CHROM-$START-$END.snp
	tail -n+2 $SNPCHUNK >> $SNPOUT
	rm $SNPCHUNK
	
	INDELCHUNK=$DATADIR/$SAMPLE.varscan.$CHROM-$START-$END.indel
	tail -n+2 $INDELCHUNK >> $INDELOUT
	rm $INDELCHUNK
    done
done

# ======================
# varscan processSomatic
# ======================

varscan processSomatic $SNPOUT --p-value 0.05
varscan processSomatic $INDELOUT --p-value 0.05
