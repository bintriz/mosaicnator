#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=8G

source $BIN_PATH/job.config

REF=$1
DATA=$2
OUT=$3

REFDICT=${REF/%.fasta/.dict}
REFDICT=${REFDICT/%.fa/.dict}
ALLDATA=${DATA/passed/all}
ALLDATA=${ALLDATA/%.vcf/.decomp.norm.uniq.vcf.gz}
Q20DATA=${ALLDATA/all.somatic.indels/q20.somatic.indels}
DATAMD5=$(dirname $DATA)/checksum/$(basename $DATA).md5
OUTMD5=$(dirname $OUT)/checksum/$(basename $OUT).md5

if [[ -f $DATA && -f $DATAMD5 && \
        $(md5sum $DATA|cut -f1 -d' ') = \
        $(cut -f1 -d' ' $DATAMD5) ]]; then

    $BIN_PATH/vcf_simplify.sh -r $REF ${DATA/passed/all}
    $BCFTOOLS filter -i 'SGT="ref->het" && QSI >= 20' -o $Q20DATA -O z $ALLDATA

    printf "#chr\tpos\tref\talt\tclone_f\tcl_total_reads\tcl_ref_count\tcl_alt_count\ttissue_f\tti_total_reads\tti_ref_count\tti_alt_count\n" > $OUT
    $BCFTOOLS query -f "%CHROM\t%POS\t%REF\t%ALT[\t%DP\t%TAR{0}\t%TIR{0}\t%TOR{0}]\n" $Q20DATA \
        |perl -ane '
        ($chr, $pos, $ref, $alt, 
         $ti_dp, $ti_tar, $ti_tir, $ti_tor, 
         $cl_dp, $cl_tar, $cl_tir, $cl_tor) = @F; 
        $cl_ref_count = $cl_tar;
        $cl_alt_count = $cl_tir;
        $cl_total_reads = $cl_ref_count + $cl_alt_count;
        if ($cl_total_reads == 0) {
            $clone_f = -1; 
        } else {
            $clone_f = $cl_alt_count / $cl_total_reads;
        }
        $ti_ref_count = $ti_tar;
        $ti_alt_count = $ti_tir;
        $ti_total_reads = $ti_ref_count + $ti_alt_count;
        if ($ti_total_reads == 0) {
            $tissue_f = -1;
        } else {
            $tissue_f = $ti_alt_count / $ti_total_reads;
        }
        print "$chr\t$pos\t$ref\t$alt\t$clone_f\t$cl_total_reads\t$cl_ref_count\t$cl_alt_count\t$tissue_f\t$ti_total_reads\t$ti_ref_count\t$ti_alt_count\n"
        ' >> $OUT
    if [[ $? = 0 ]]; then
        mkdir -p $(dirname $OUTMD5)
        md5sum $OUT > $OUTMD5
    fi
else
    echo "$DATA doesn't exist or doesn't match to the checksum."
    exit 1
fi
