#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=12G

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
INTERVAL=$5
CHECKSUMDIR=$(dirname $OUTPREFIX)/checksum
MD5PREFIX=$CHECKSUMDIR/$(basename $OUTPREFIX)

if [ -f $OUTPREFIX.txt ] && [ -f $MD5PREFIX.txt.md5 ] && \
       [ "$(md5sum $OUTPREFIX.txt)" = "$(cat $MD5PREFIX.txt.md5)" ]; then
    echo "$OUTPREFIX.txt exists and matches to the checksum"
    exit 0
else
    rm -rf $OUTPREFIX.txt $MD5PREFIX.txt.md5
fi

mutect 8 -I:tumor $CLONEBAM -I:normal $TISSUEBAM --out $OUTPREFIX.txt --only_passing_calls -R $REF -L $INTERVAL

mkdir -p $CHECKSUMDIR
md5sum $OUTPREFIX.txt > $MD5PREFIX.txt.md5
