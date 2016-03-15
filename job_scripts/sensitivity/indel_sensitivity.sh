#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=8G

. ~/.bash_profile > /dev/null

AF=$1
TRUEFILE=$2
DATADIR=$3
OUTFILE=$4
OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5
SAMPLE=$(basename $OUTFILE)
SAMPLE=${SAMPLE/.indel_sensitivity_*AFcutoff.txt}

for i in 1 2 3; do
    DATAFILE=$DATADIR/$SAMPLE.call_n$i.indel_AF.txt
    DATAMD5=$DATADIR/checksum/$(basename $DATAFILE).md5
    if [ ! -f $DATAFILE ] || [ ! -f $DATAMD5 ] || \
        [ "$(md5sum $DATAFILE|cut -f1 -d' ')" != "$(cut -f1 -d' ' $DATAMD5)" ]; then
        echo "$DATAFILE doesn't exist or doesn't match to the checksum."
        exit 1
    fi
done

printf "#sample\tcallset\tpositive_n\ttruepositive_n\ttrue_n\textra_call\tsensitivity\n" > $OUTFILE
TRUE_N=$(cat $TRUEFILE|wc -l)
for i in 1 2 3; do
    POS_N=$(eval tail -qn+2 $DATADIR/$SAMPLE.call_n{$i..3}.indel_AF.txt|wc -l)
    TRUEPOS_N=$(eval tail -qn+2 $DATADIR/$SAMPLE.call_n{$i..3}.indel_AF.txt \
            |cut -f-4|sort -S3G|comm -12 <(sort -S4G $TRUEFILE) -|wc -l)
    EXT_CALL=$(($POS_N-$TRUEPOS_N))
    SENS=$(echo $TRUEPOS_N $TRUE_N|awk '{printf("%.6f", $1/$2)}')
    printf "$SAMPLE\tcall_n{$i..3}\t$POS_N\t$TRUEPOS_N\t$TRUE_N\t$EXT_CALL\t$SENS\n" >> $OUTFILE
done
for i in 2 3; do
    POS_N=$(eval tail -qn+2 $DATADIR/$SAMPLE.call_n{$i..3}.indel_AF.txt \
            |awk -v af=$AF '$5 >= af'|wc -l)
    TRUEPOS_N=$(eval tail -qn+2 $DATADIR/$SAMPLE.call_n{$i..3}.indel_AF.txt \
            |awk -v af=$AF '$5 >= af' \
            |cut -f-4|sort -S3G|comm -12 <(sort -S4G $TRUEFILE) -|wc -l)
    EXT_CALL=$(($POS_N-$TRUEPOS_N))
    SENS=$(echo $TRUEPOS_N $TRUE_N|awk '{printf("%.6f", $1/$2)}')
    printf "$SAMPLE\tcall_n{$i..3}+${AF/0./}AFcutoff\t$POS_N\t$TRUEPOS_N\t$TRUE_N\t$EXT_CALL\t$SENS\n" >> $OUTFILE
done
for CALLER in scalpel strelka varscan; do
    POS_N=$(tail -qn+2 $DATADIR/$SAMPLE.$CALLER.indel_AF.txt|wc -l)
    TRUEPOS_N=$(tail -qn+2 $DATADIR/$SAMPLE.$CALLER.indel_AF.txt \
            |cut -f-4|sort -S3G|comm -12 <(sort -S4G $TRUEFILE) -|wc -l)
    EXT_CALL=$(($POS_N-$TRUEPOS_N))
    SENS=$(echo $TRUEPOS_N $TRUE_N|awk '{printf("%.6f", $1/$2)}')
    printf "$SAMPLE\t$CALLER\t$POS_N\t$TRUEPOS_N\t$TRUE_N\t$EXT_CALL\t$SENS\n" >> $OUTFILE
done

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
