#!/bin/bash
#$ -q 1-day
#$ -cwd

BIN_PATH="$(readlink -f ${BASH_SOURCE[0]}|xargs dirname)/../.."

FLIST=$1
OUT=$2

OUTMD5=$(dirname $OUT)/checksum/$(basename $OUT).md5

for CONCALL in $(cat $FLIST); do
    CONCALLMD5=$(dirname $CONCALL)/checksum/$(basename $CONCALL).md5
    if [[ ! -f $CONCALL || ! -f $CONCALLMD5 || \
            $(md5sum $CONCALL|cut -f1 -d' ') != \
            $(cut -f1 -d' ' $CONCALLMD5) ]]; then
        echo "$CONCALL doesn't exist or doesn't match to the checksum."
        exit 1
    fi
done

$BIN_PATH/expl_score.py $FLIST > $OUT
if [[ $? = 0 ]]; then
    mkdir -p $(dirname $OUTMD5)
    md5sum $OUT > $OUTMD5
fi
