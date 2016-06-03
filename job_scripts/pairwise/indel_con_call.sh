#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=8G

BIN_PATH="$(readlink -f ${BASH_SOURCE[0]}|xargs dirname)/../.."
source $BIN_PATH/job.config

AF=$1
DATADIR=$2
OUT=$3
OUTMD5=$(dirname $OUT)/checksum/$(basename $OUT).md5
SAMPLE=$(basename $OUT .indel_call_n3_${AF/0./}AFcutoff.txt)

for CALLER in scalpel strelka varscan; do
    DATA=$DATADIR/$SAMPLE.$CALLER.indel_AF.txt
    DATAMD5=$DATADIR/checksum/$SAMPLE.$CALLER.indel_AF.txt.md5
    if [[ ! -f $DATA || ! -f $DATAMD5 || \
            $(md5sum $DATA|cut -f1 -d' ') != \
            $(cut -f1 -d' ' $DATAMD5) ]]; then
        echo "$DATA doesn't exist or doesn't match to the checksum."
        exit 1
    fi    
done

for i in 1 2 3; do
    CONCALL=$DATADIR/$SAMPLE.call_n$i.indel_AF.txt
    printf "#chr\tpos\tref\talt\tindel_AF\n" > $CONCALL
    tail -qn+2 $DATADIR/$SAMPLE.{scalpel,strelka,varscan}.indel_AF.txt \
        |$Q -t "SELECT c1, c2, c3, c4, sum(c5)/count(*), count(*) FROM - GROUP BY c1, c2, c3, c4" \
        |awk -v n=$i '$6 == n' \
        |cut -f-5 \
        |sort -k1,1V -k2,2n -S7G >> $CONCALL
done

CALL_N3=$DATADIR/$SAMPLE.call_n3.indel_AF.txt
printf "#chr\tpos\tref\talt\tindel_AF\n" > $OUT
tail -n+2 $CALL_N3 |awk -v af=$AF '$5 >= af' >> $OUT
if [[ $? = 0 ]]; then
    mkdir -p $(dirname $OUTMD5)
    md5sum $OUT > $OUTMD5
fi
