#!/bin/bash
#$ -q 4-days
#$ -cwd

. ~/.bash_profile > /dev/null

MINMQ=$1
MINBQ=$2
CLONEBAM=$3
TISSUEBAM=$4
COORDFILE=$5
OUTFILE=$6

COORDMD5=$(dirname $COORDFILE)/checksum/$(basename $COORDFILE).md5
OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5

if [ ! -f $COORDFILE ] || [ ! -f $COORDMD5 ] || \
       [ "$(md5sum $COORDFILE)" != "$(cat $COORDMD5)" ]; then
    echo "$COORDFILE doesn't exist or doesn't match to the checksum."
    exit 1
fi

snv_af.py -c $CLONEBAM -t $TISSUEBAM -q $MINMQ -Q $MINBQ $COORDFILE > $OUTFILE

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
rm -rf $COORDFILE $COORDMD5
