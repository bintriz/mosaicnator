#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=32G

. ~/.bash_profile > /dev/null

REF=$1
DATAFILE=$2
OUTFILE=$3

REFDICT=${REF/%fasta/dict}
REFDICT=${REFDICT/%fa/dict}
DATAMD5=$(dirname $DATAFILE)/checksum/$(basename $DATAFILE).md5
OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5

if [ ! -f $DATAFILE ] || [ ! -f $DATAMD5 ] || \
       [ "$(md5sum $DATAFILE|cut -f1 -d' ')" != "$(cut -f1 -d' ' $DATAMD5)" ]; then
    echo "$DATAFILE doesn't exist or doesn't match to the checksum."
    exit 1
fi

var2vcf.py -f varscan -d $REFDICT $DATAFILE $DATAFILE.vcf
vcf_simplify.sh -r $REF $DATAFILE.vcf
rm $DATAFILE.vcf

printf "#chr\tpos\tref\talt\tclone_f\tcl_total_reads\tcl_ref_count\tcl_alt_count\ttissue_f\tti_total_reads\tti_ref_count\tti_alt_count\n" > $OUTFILE
bcftools query -f \
	 "%CHROM\t%POS\t%REF\t%ALT\t%tumor_reads1\t%tumor_reads2\t%normal_reads1\t%normal_reads2\n" \
	 $DATAFILE.decomp.norm.uniq.vcf.gz \
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
    }' >> $OUTFILE

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
