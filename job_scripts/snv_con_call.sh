#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

SAMPLE=$1
AF=$2
DATADIR=$3
OUTDIR=$4

for CALLER in mutect somaticsniper strelka varscan; do
    DATAFILE=$DATADIR/$SAMPLE.$CALLER.snv_AF.txt
    DATAMD5=$DATADIR/checksum/$SAMPLE.$CALLER.snv_AF.txt.md5
    if [ ! -f $DATAFILE ] || [ ! -f $DATAMD5 ] || \
	   [ "$(md5sum $DATAFILE)" != "$(cat $DATAMD5)" ]; then
	echo "$DATAFILE doesn't exist or doesn't match to the checksum."
	exit 1
    fi    
done

for i in 1 2 3 4; do
    CONCALL=$DATADIR/$SAMPLE.call_n$i.snv_AF.txt
    printf "#chr\tpos\tref\talt\tsnv_AF\n" > $CONCALL
    tail -qn+2 $DATADIR/$SAMPLE.{mutect,somaticsniper,strelka,varscan}.snv_AF.txt \
	|cut -f-5 \
	|q -t "SELECT c1, c2, c3, c4, c5, count(*) FROM - GROUP BY c1, c2, c3, c4, c5" \
	|awk -v CALL_N=$i '$6 == call_n' \
	|cut -f-5 >> $CONCALL
done

CALL_N4=$DATADIR/$SAMPLE.call_n4.snv_AF.txt
CUTOFF=$OUTDIR/$SAMPLE.snv_call_n4_${AF/0./}AFcutoff.txt
CUTOFFMD5=$OUTDIR/checksum/$(basename $CUTOFF).md5

printf "#chr\tpos\tref\talt\tsnv_AF\n" > $CUTOFF
tail -n+2 $CALL_N4 \
    |awk -v AF=$AF '$5 >= af' >> $CUTOFF

mkdir -p $(dirname $CUTOFFMD5)
md5sum $CUTOFF > $CUTOFFMD5
