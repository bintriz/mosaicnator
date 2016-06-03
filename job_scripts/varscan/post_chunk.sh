#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=16G

BIN_PATH="$(readlink -f ${BASH_SOURCE[0]}|xargs dirname)/../.."
source $BIN_PATH/job.config

VARSCAN="$JAVA -Xmx4g -jar $VARSCAN_JAR"

PREFIX=$1
CHUNKFILE=$2
MD5PREFIX=$(dirname $PREFIX)/checksum/$(basename $PREFIX)

# =============
# varscan merge
# =============

SNPOUT=$PREFIX.snp
INDELOUT=$PREFIX.indel
trap "rm -f $SNPOUT $INDELOUT" ERR

head -n1 $(ls $PREFIX.*.snp|head -n1) > $SNPOUT
head -n1 $(ls $PREFIX.*.indel|head -n1) > $INDELOUT

for INTERVAL in $(cat $CHUNKFILE); do
    SNPCHUNK=$PREFIX.${INTERVAL/:/-}.snp
    SNPCHUNKMD5=$MD5PREFIX.${INTERVAL/:/-}.snp.md5
    
    if [[ -f $SNPCHUNK && -f $SNPCHUNKMD5 && \
            $(md5sum $SNPCHUNK|cut -f1 -d' ') = \
            $(cut -f1 -d' ' $SNPCHUNKMD5) ]]; then
        tail -n+2 $SNPCHUNK >> $SNPOUT
    else
        echo "$SNPCHUNK doesn't exist or doesn't match to the checksum."
        exit 1
    fi
    
    INDELCHUNK=$PREFIX.${INTERVAL/:/-}.indel
    INDELCHUNKMD5=$MD5PREFIX.${INTERVAL/:/-}.indel.md5
	
    if [[ -f $INDELCHUNK && -f $INDELCHUNKMD5 && \
            $(md5sum $INDELCHUNK|cut -f1 -d' ') = \
            $(cut -f1 -d' ' $INDELCHUNKMD5) ]]; then
        tail -n+2 $INDELCHUNK >> $INDELOUT
    else
        echo "$INDELCHUNK doesn't exist or doen't match to the checksum."
        exit 1
    fi
done

# =============================================================
# varscan processSomatic, create checksum, & remove chunk files
# =============================================================

$VARSCAN processSomatic $SNPOUT --p-value 0.05
if [[ $? = 0 ]]; then
    md5sum $SNPOUT.Somatic.hc > $MD5PREFIX.snp.Somatic.hc.md5
    rm -f $PREFIX.*-*-*.snp $MD5PREFIX.*-*-*.snp.md5 
fi

$VARSCAN processSomatic $INDELOUT --p-value 0.05
if [[ $? = 0 ]]; then
    md5sum $INDELOUT.Somatic.hc > $MD5PREFIX.indel.Somatic.hc.md5
    rm -f $PREFIX.*-*-*.indel $MD5PREFIX.*-*-*.indel.md5
fi 
