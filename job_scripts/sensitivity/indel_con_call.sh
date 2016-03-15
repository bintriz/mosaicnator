#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=8G

. ~/.bash_profile > /dev/null

AF=$1
DATADIR=$2
SAMPLE=$3

for CALLER in scalpel strelka varscan; do
    DATAFILE=$DATADIR/$SAMPLE.$CALLER.indel_AF.txt
    DATAMD5=$DATADIR/checksum/$SAMPLE.$CALLER.indel_AF.txt.md5
    if [ ! -f $DATAFILE ] || [ ! -f $DATAMD5 ] || \
        [ "$(md5sum $DATAFILE|cut -f1 -d' ')" != "$(cut -f1 -d' ' $DATAMD5)" ]; then
        echo "$DATAFILE doesn't exist or doesn't match to the checksum."
        exit 1
    fi    
done

for i in 1 2 3; do
    CONCALL=$DATADIR/$SAMPLE.call_n$i.indel_AF.txt
    CONCALLMD5=$DATADIR/checksum/$(basename $CONCALL).md5
    printf "#chr\tpos\tref\talt\tindel_AF\n" > $CONCALL
    tail -qn+2 $DATADIR/$SAMPLE.{scalpel,strelka,varscan}.indel_AF.txt \
        |q -t "SELECT c1, c2, c3, c4, sum(c5)/count(*), count(*) FROM - GROUP BY c1, c2, c3, c4" \
        |awk -v n=$i '$6 == n' \
        |cut -f-5 \
        |sort -k1,1V -k2,2n -S7G >> $CONCALL
    md5sum $CONCALL > $CONCALLMD5
done