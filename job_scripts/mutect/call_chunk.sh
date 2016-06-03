#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=12G

BIN_PATH="$(readlink -f ${BASH_SOURCE[0]}|xargs dirname)/../.."
source $BIN_PATH/job.config

if [[ -f $GATK_KEY ]]; then
    MUTECT="$JAVA7 -Xmx8g -jar $MUTECT_JAR -T MuTect -et NO_ET -K $GATK_KEY
    --logging_level ERROR --only_passing_calls"
else
    MUTECT="$JAVA7 -Xmx8g -jar $MUTECT_JAR -T MuTect
    --logging_level ERROR --only_passing_calls"
fi

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
OUTPREFIX=$4
CHUNKFILE=$5
INTERVAL=$(awk "NR==${SGE_TASK_ID}" $CHUNKFILE)
OUTPREFIX=$OUTPREFIX.${INTERVAL/:/-}
CHECKSUMDIR=$(dirname $OUTPREFIX)/checksum
MD5PREFIX=$CHECKSUMDIR/$(basename $OUTPREFIX)

if [[ -f $OUTPREFIX.txt && -f $MD5PREFIX.txt.md5 && \
        $(md5sum $OUTPREFIX.txt|cut -f1 -d' ') = \
        $(cut -f -d' ' $MD5PREFIX.txt.md5) ]]; then
    echo "$OUTPREFIX.txt exists and matches to the checksum"
else
    rm -f $OUTPREFIX.txt $MD5PREFIX.txt.md5
    $MUTECT -R $REF -L $INTERVAL \
        -I:tumor $CLONEBAM -I:normal $TISSUEBAM \
        --out $OUTPREFIX.txt
    if [[ $? = 0 ]]; then
        mkdir -p $CHECKSUMDIR
        md5sum $OUTPREFIX.txt > $MD5PREFIX.txt.md5
    fi
fi
