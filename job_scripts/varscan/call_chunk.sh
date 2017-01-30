#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=16G

source $BIN_PATH/job.config

VARSCAN="$JAVA -Xmx8g -jar $VARSCAN_JAR"

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
CHUNKFILE=$5
INTERVAL=$(awk "NR==${SGE_TASK_ID}" $CHUNKFILE)
OUTPREFIX=$OUTPREFIX.${INTERVAL/:/-}
CHECKSUMDIR=$(dirname $OUTPREFIX)/checksum
MD5PREFIX=$CHECKSUMDIR/$(basename $OUTPREFIX)

if [[ -f $OUTPREFIX.snp && -f $MD5PREFIX.snp.md5 && \
        $(md5sum $OUTPREFIX.snp|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $MD5PREFIX.snp.md5) && \
        -f $OUTPREFIX.indel && -f $MD5PREFIX.indel.md5 && \
        $(md5sum $OUTPREFIX.indel|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $MD5PREFIX.indel.md5) ]]; then
    echo "$OUTPREFIX.snp/indel exist and match to the corresponding checksum."
else
    rm -f $OUTPREFIX.snp $MD5PREFIX.snp.md5 $OUTPREFIX.indel $MD5PREFIX.indel.md5
    if [[ $($SAMTOOLS mpileup -f $REF -r $INTERBAL $TISSUEBAM $CLONEBAM|head|wc -l) = 0 ]]; then
        touch $OUTPREFIX.snp $OUTPREFIX.indel
    else
        $SAMTOOLS mpileup -f $REF -r $INTERVAL $TISSUEBAM $CLONEBAM \
            |$VARSCAN somatic --mpileup $OUTPREFIX
    fi
    if [[ $? = 0 ]]; then
        mkdir -p $CHECKSUMDIR
        md5sum $OUTPREFIX.snp > $MD5PREFIX.snp.md5
        md5sum $OUTPREFIX.indel > $MD5PREFIX.indel.md5
    fi
fi
