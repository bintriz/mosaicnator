#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=8G

AF=$1
TRUE=$2
DATADIR=$3
OUT=$4
OUTMD5=$(dirname $OUT)/checksum/$(basename $OUT).md5
SAMPLE=$(basename $OUT)
SAMPLE=${SAMPLE/.snv_sensitivity_*AFcutoff.txt}

for i in 1 2 3 4; do
    DATA=$DATADIR/$SAMPLE.call_n$i.snv_AF.txt
    DATAMD5=$DATADIR/checksum/$(basename $DATA).md5
    if [[ ! -f $DATA || ! -f $DATAMD5 || \
            $(md5sum $DATA|cut -f1 -d' ') != \
            $(cut -f1 -d' ' $DATAMD5) ]]; then
        echo "$DATA doesn't exist or doesn't match to the checksum."
        exit 1
    fi
done

printf "#sample\tcallset\tpositive_n\ttruepositive_n\ttrue_n\textra_call\tsensitivity\n" > $OUT
TRUE_N=$(cat $TRUE|wc -l)
for i in 1 2 3 4; do
    POS_N=$(eval tail -qn+2 $DATADIR/$SAMPLE.call_n{$i..4}.snv_AF.txt|wc -l)
    TRUEPOS_N=$(eval tail -qn+2 $DATADIR/$SAMPLE.call_n{$i..4}.snv_AF.txt \
		       |cut -f-4|sort -S3G|comm -12 <(sort -S4G $TRUE) -|wc -l)
    EXT_CALL=$(($POS_N-$TRUEPOS_N))
    SENS=$(echo $TRUEPOS_N $TRUE_N|awk '{printf("%.6f", $1/$2)}')
    printf "$SAMPLE\tcall_n{$i..4}\t$POS_N\t$TRUEPOS_N\t$TRUE_N\t$EXT_CALL\t$SENS\n" >> $OUT
done
for i in 3 4; do
    POS_N=$(eval tail -qn+2 $DATADIR/$SAMPLE.call_n{$i..4}.snv_AF.txt \
		   |awk -v af=$AF '$5 >= af'|wc -l)
    TRUEPOS_N=$(eval tail -qn+2 $DATADIR/$SAMPLE.call_n{$i..4}.snv_AF.txt \
		       |awk -v af=$AF '$5 >= af' \
		       |cut -f-4|sort -S3G|comm -12 <(sort -S4G $TRUE) -|wc -l)
    EXT_CALL=$(($POS_N-$TRUEPOS_N))
    SENS=$(echo $TRUEPOS_N $TRUE_N|awk '{printf("%.6f", $1/$2)}')
    printf "$SAMPLE\tcall_n{$i..4}+${AF/0./}AFcutoff\t$POS_N\t$TRUEPOS_N\t$TRUE_N\t$EXT_CALL\t$SENS\n" >> $OUT
done
for CALLER in mutect somaticsniper strelka varscan; do
    POS_N=$(tail -qn+2 $DATADIR/$SAMPLE.$CALLER.snv_AF.txt|wc -l)
    TRUEPOS_N=$(tail -qn+2 $DATADIR/$SAMPLE.$CALLER.snv_AF.txt \
		       |cut -f-4|sort -S3G|comm -12 <(sort -S4G $TRUE) -|wc -l)
    EXT_CALL=$(($POS_N-$TRUEPOS_N))
    SENS=$(echo $TRUEPOS_N $TRUE_N|awk '{printf("%.6f", $1/$2)}')
    printf "$SAMPLE\t$CALLER\t$POS_N\t$TRUEPOS_N\t$TRUE_N\t$EXT_CALL\t$SENS\n" >> $OUT
done

if [[ $? = 0 ]]; then
    mkdir -p $(dirname $OUTMD5)
    md5sum $OUT > $OUTMD5
fi
