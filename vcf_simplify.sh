#!/bin/bash

# Usage info
usage() {
    cat <<EOF

Usage: ${0##*/} [options] <in.vcf>

Simplify in.vcf by decomposing multiallelic sites, normalizing variants, 
decomposing biallelic block substitutions, and dropping duplicates

    -h            display this help and exit
    -n            do not fail when REF is inconsistent with reference sequence for non SNPs
    -r ref.fasta  reference sequence fasta file (required)
    -s            sort before simplifying

EOF
}

# Process options
nflag=""
while getopts ":hnr:s" opt; do
    case "$opt" in
	h  ) usage; exit 0;;
	n  ) nflag="-n";;
	r  ) ref=$OPTARG;;
	s  ) sflag="-s";;
	\? ) echo "Unknow option: -$OPTARG" >&2
	     usage >&2; exit 1;;
	:  ) echo "Missing option argumnet for -$OPTARG" >&2
	     usage >&2; exit 1;;
    esac
done
shift "$((OPTIND-1))"
in_vcf=$1

if [ -z $ref ]; then
    echo "-r must be set." >&2
    usage >&2; exit 1
elif [ ! -e $ref ]; then
    echo "$ref file doesn't exist." >&2; exit 1
elif [ -z $in_vcf ]; then
    echo "Input vcf file must be set." >&2
    usage >&2; exit 1
elif [ ! -e $in_vcf ]; then
    echo "$in_vcf file doesn't exist." >&2; exit 1
fi

# Check input file.
if [[ $in_vcf =~ .vcf$ ]]; then
    CATCMD=cat
    out_name=${in_vcf/%.vcf/}
elif [[ $in_vcf =~ .vcf.gz$ ]]; then
    CATCMD=zcat
    out_name=${in_vcf/%.vcf.gz/}
elif [[ $in_vcf =~ .vcf.bz2$ ]]; then
    CATCMD=bzcat
    out_name=${in_vcf/%.vcf.bz2/}
else
    echo "$in_vcf file isn't one of vcf, vcf.gz, and vcf.bz2." >&2; exit 1
fi

# Main
out_vcf=$out_name.decomp.norm.uniq.vcf.gz
out_log=$out_name.decomp.norm.uniq.log
config=$(readlink -f ${BASH_SOURCE[0]})/job.config
eval $(grep ^VT $config)

if [ ! -z $sflag ]; then
    $CATCMD $in_vcf \
	|$VT sort - \
	|$VT decompose                - 2> $out_log.tmp1 \
	|$VT normalize -r $ref $nflag - 2> $out_log.tmp2 \
	|$VT uniq      -o $out_vcf    - 2> $out_log.tmp3	  
else
    $CATCMD $in_vcf \
	|$VT decompose                - 2> $out_log.tmp1 \
	|$VT normalize -r $ref $nflag - 2> $out_log.tmp2 \
	|$VT uniq      -o $out_vcf    - 2> $out_log.tmp3
fi

cat $out_log.tmp{1,2,3} |tee $out_log
rm $out_log.tmp{1,2,3}
