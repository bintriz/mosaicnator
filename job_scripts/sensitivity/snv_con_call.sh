#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=8G

AF=$1
DATADIR=$2
SAMPLE=$3

for CALLER in mutect somaticsniper strelka varscan; do
    DATA=$DATADIR/$SAMPLE.$CALLER.snv_AF.txt
    DATAMD5=$DATADIR/checksum/$SAMPLE.$CALLER.snv_AF.txt.md5
    if [[ ! -f $DATA || ! -f $DATAMD5 || \
            $(md5sum $DATA|cut -f1 -d' ') != \
            $(cut -f1 -d' ' $DATAMD5) ]]; then
        echo "$DATA doesn't exist or doesn't match to the checksum."
        exit 1
    fi    
done

for i in 1 2 3 4; do
    CONCALL=$DATADIR/$SAMPLE.call_n$i.snv_AF.txt
    CONCALLMD5=$DATADIR/checksum/$(basename $CONCALL).md5

    printf "#chr\tpos\tref\talt\tsnv_AF\n" > $CONCALL
    tail -qn+2 $DATADIR/$SAMPLE.{mutect,somaticsniper,strelka,varscan}.snv_AF.txt \
        |cut -f-5 \
        |sort -k1,1V -k2,2n -S7G \
        |uniq -c \
        |awk -v n=$i '$1 == n {print $2"\t"$3"\t"$4"\t"$5"\t"$6}' >> $CONCALL

    if [[ $? = 0 ]]; then
        md5sum $CONCALL > $CONCALLMD5
    fi
done
