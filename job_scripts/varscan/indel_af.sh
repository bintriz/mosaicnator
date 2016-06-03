#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=32G

BIN_PATH="$(readlink -f ${BASH_SOURCE[0]}|xargs dirname)/../.."
source $BIN_PATH/job.config

REF=$1
DATA=$2
OUT=$3

REFDICT=${REF/%fasta/dict}
REFDICT=${REFDICT/%fa/dict}
DATAMD5=$(dirname $DATA)/checksum/$(basename $DATA).md5
OUTMD5=$(dirname $OUT)/checksum/$(basename $OUT).md5

if [[ -f $DATA && -f $DATAMD5 && \
        $(md5sum $DATA|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $DATAMD5) ]]; then
    $BIN_PATH/var2vcf.py -f varscan -d $REFDICT $DATA $DATA.vcf
    $BIN_PATH/vcf_simplify.sh -r $REF $DATA.vcf

    printf "#chr\tpos\tref\talt\tclone_f\tcl_total_reads\tcl_ref_count\tcl_alt_count\ttissue_f\tti_total_reads\tti_ref_count\tti_alt_count\n" > $OUT
    $BCFTOOLS query -f "%CHROM\t%POS\t%REF\t%ALT\t%tumor_reads1\t%tumor_reads2\t%normal_reads1\t%normal_reads2\n" \
        $DATA.decomp.norm.uniq.vcf.gz \
        |awk '
    {
        cl_ref_count = $5
        cl_alt_count = $6
        cl_total_reads = cl_ref_count + cl_alt_count
        clone_f = cl_alt_count / cl_total_reads
        ti_ref_count = $7
       	ti_alt_count = $8
       	ti_total_reads = ti_ref_count + ti_alt_count
       	tissue_f = ti_alt_count / ti_total_reads
       	print $1"\t"$2"\t"$3"\t"$4"\t"clone_f"\t"cl_total_reads"\t"cl_ref_count"\t"cl_alt_count"\t"tissue_f"\t"ti_total_reads"\t"ti_ref_count"\t"ti_alt_count
    }' >> $OUT
    if [[ $? = 0 ]]; then
        mkdir -p $(dirname $OUTMD5)
        md5sum $OUT > $OUTMD5
        rm -f $DATA.vcf
    fi
else
    echo "$DATA doesn't exist or doesn't match to the checksum."
    exit 1
fi
