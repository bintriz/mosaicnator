#!/bin/bash
#$ -q 4-days
#$ -cwd

MINMQ=$1
MINBQ=$2
CLONEBAM=$3
TISSUEBAM=$4
DATA=$5
OUT=$6

COORD=${OUT/snv_AF.txt/snv_coord.txt}
DATAMD5=$(dirname $DATA)/checksum/$(basename $DATA).md5
OUTMD5=$(dirname $OUT)/checksum/$(basename $OUT).md5

if [[ -f $DATA && -f $DATAMD5 && \
        $(md5sum $DATA|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $DATAMD5) ]]; then
    tail -n+2 $DATA \
        |cut -f-4 \
        |perl -ne '
    my ($chr, $pos, $ref, $alt) = split /\t/;
    chomp($alt);
    grep { print "$chr\t$pos\t$ref\t$_\n" } split /,/, $alt;
    ' > $COORD
    $BIN_PATH/snv_af.py -c $CLONEBAM -t $TISSUEBAM -q $MINMQ -Q $MINBQ $COORD > $OUT
    if [[ $? = 0 ]]; then
        mkdir -p $(dirname $OUTMD5)
        md5sum $OUT > $OUTMD5
    fi
    rm -f $COORD
else
    echo "$DATA doesn't exist or doesn't match to the checksum."
    exit 1
fi
