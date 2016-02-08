#!/bin/bash
#$ -q 1-days
#$ -cwd

. ~/.bash_profile > /dev/null

FLIST=$1
OUTFILE=$2

OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5

for CONCALL in $(cat $FLIST); do
    CONCALLMD5=$(dirname $CONCALL)/checksum/$(basename $CONCALL).md5
    if [ ! -f $CONCALL ] || [ ! -f $CONCALLMD5 ] || \
	   [ "$(md5sum $CONCALL|cut -f1 -d' ')" != "$(cut -f1 -d' ' $CONCALLMD5)" ]; then
	echo "$CONCALL doesn't exist or doesn't match to the checksum."
	exit 1
    fi
done

expl_score.py $FLIST > $OUTFILE

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
