#!/bin/bash
#$ -q 1-day
#$ -cwd

source $BIN_PATH/job.config

REF=$1
DATA=$2
OUT=$3

DATAMD5=$(dirname $DATA)/checksum/$(basename $DATA).md5
OUTMD5=$(dirname $OUT)/checksum/$(basename $OUT).md5

if [[ -f $DATA && -f $DATAMD5 && \
        $(md5sum $DATA|cut -f1 -d' ') =\
        $(cut -f1 -d' ' $DATAMD5) ]]; then
    $BIN_PATH/vcf_simplify.sh -r $REF $DATA
    printf "#chr\tpos\tref\talt\tclone_f\tcl_total_reads\tcl_ref_count\tcl_alt_count\n" \
        > $OUT
    $BCFTOOLS query -f "%CHROM\t%POS\t%REF\t%ALT\t%COVRATIO[\t%DP\t%AD{0}\t%AD{1}]\n" \
        ${DATA/%vcf.gz/decomp.norm.uniq.vcf.gz} >> $OUT

    if [[ $? = 0 ]]; then
        mkdir -p $(dirname $OUTMD5)
        md5sum $OUT > $OUTMD5
    fi
else
    echo "$DATA doesn't exist or doesn't match to the checksum."
    exit 1
fi
