#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

REF=$1
DATAFILE=$2
OUTFILE=$3

DATAMD5=$(dirname $DATAFILE)/checksum/$(basename $DATAFILE).md5
OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5

if [ ! -f $DATAFILE ] || [ ! -f $DATAMD5 ] || \
    [ "$(md5sum $DATAFILE|cut -f1 -d' ')" != "$(cut -f1 -d' ' $DATAMD5)" ]; then
    echo "$DATAFILE doesn't exist or doesn't match to the checksum."
    exit 1
fi

vcf_simplify.sh -r $REF $DATAFILE
printf "#chr\tpos\tref\talt\tclone_f\tcl_total_reads\tcl_ref_count\tcl_alt_count\n" \
    > $OUTFILE
bcftools query -f "%CHROM\t%POS\t%REF\t%ALT\t%COVRATIO[\t%DP\t%AD{0}\t%AD{1}]\n" \
    ${DATAFILE/%vcf.gz/decomp.norm.uniq.vcf.gz} >> $OUTFILE

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
