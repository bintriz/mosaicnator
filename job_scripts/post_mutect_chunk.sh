#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

PREFIX=$1
CHUNKFILE=$2
MD5PREFIX=$(dirname $PREFIX)/checksum/$(basename $PREFIX)

# ==========================
# mutect filter KEEP & merge
# ==========================

OUTFILE=$PREFIX.keep.txt
OUTMD5=$MD5PREFIX.keep.txt.md5

head -n2 $(ls $PREFIX.*.txt|head -n1) > $OUTFILE
for INTERVAL in $(cat $CHUNKFILE); do
    CHUNKFILE=$PREFIX.${INTERVAL/:/-}.txt
    CHUNKMD5=$MD5PREFIX.${INTERVAL/:/-}.txt.md5
    
    if [ -f $CHUNKFILE ] && [ -f $CHUNKMD5 ] && \
	   [ "$(md5sum $CHUNKFILE)" = "$(cat $CHUNKMD5)" ]; then
	tail -n+3 $CHUNKFILE |grep KEEP$ >> $OUTFILE
    else
	echo "$CHUNKFILE doesn't exist or doesn't match to the checksum."
	exit 1
    fi
done

# ====================================
# Create checksum & Remove chunk files
# ====================================

md5sum $OUTFILE > $OUTMD5
rm -rf $PREFIX.*-*-*.txt $MD5PREFIX.*-*-*.txt.md5
