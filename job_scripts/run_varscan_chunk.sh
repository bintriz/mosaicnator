#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=16G

. ~/.bash_profile > /dev/null

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
CHUNKFILE=$5
INTERVAL=$(awk "NR==${SGE_TASK_ID}" $CHUNKFILE)
OUTPREFIX=$OUTPREFIX.${INTERVAL/:/-}
CHECKSUMDIR=$(dirname $OUTPREFIX)/checksum
MD5PREFIX=$CHECKSUMDIR/$(basename $OUTPREFIX)

if [ -f $OUTPREFIX.snp ] && [ -f $MD5PREFIX.snp.md5 ] && \
       [ "$(md5sum $OUTPREFIX.snp)" = "$(cat $MD5PREFIX.snp.md5)" ] && \
       [ -f $OUTPREFIX.indel ] && [ -f $MD5PREFIX.indel.md5 ] && \
       [ "$(md5sum $OUTPREFIX.indel)" = "$(cat $MD5PREFIX.indel.md5)" ]; then
    echo "$OUTPREFIX.snp/indel exist and match to the corresponding checksum."
    exit 0
else
    rm -rf $OUTPREFIX.snp $MD5PREFIX.snp.md5 $OUTPREFIX.indel $MD5PREFIX.indel.md5
fi

samtools mpileup -f $REF -r $INTERVAL $TISSUEBAM $CLONEBAM|varscan 8 somatic --mpileup $OUTPREFIX

mkdir -p $CHECKSUMDIR
md5sum $OUTPREFIX.snp > $MD5PREFIX.snp.md5
md5sum $OUTPREFIX.indel > $MD5PREFIX.indel.md5
