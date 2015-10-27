#!/bin/bash

[ $# -lt 3 ] && { echo -e "Usage:\n  $(basename "$0") ref clone.bam tissue.bam sample.name out.dir"; exit 1; }

ref=$1
tumor=$2
normal=$3
sample=$4
outdir=$5
out=$sample.scalpel

SCRIPT_PATH=$(dirname $(readlink -f ${BASH_SOURCE[0]}))

q_err=q.err/scalpel.$sample
q_out=q.out/scalpel.$sample

if [ ! -d $outdir/$out ]; then
    mkdir -p $outdir/$out
fi

if [ ! -d $q_err ]; then
    mkdir -p $q_err
fi

if [ ! -d $q_out ]; then
    mkdir -p $q_out
fi

for interval in $(samtools idxstats $tumor|awk '!/^*/ {print $1":1-"$2 }'|tac); do 
    job_name=chr${interval/:*/}.$sample
    size=${interval/*-/}
    
    if [[ $size -gt 100000000 ]]; then
	qsub -N $job_name -q lg-mem -o $q_out -e $q_err -pe threaded 20 -l h_vmem=16G \
	     $SCRIPT_PATH/scalpel.sh $ref $tumor $normal $outdir/$out/$out $interval 20
    elif [[ $size -gt 10000000 ]]; then
	qsub -N $job_name -q 4-days -o $q_out -e $q_err -pe threaded 10 -l h_vmem=12G \
	     $SCRIPT_PATH/scalpel.sh $ref $tumor $normal $outdir/$out/$out $interval 10
    else
	qsub -N $job_name -q 4-days -o $q_out -e $q_err -pe threaded 4 -l h_vmem=8G  \
	     $SCRIPT_PATH/scalpel.sh $ref $tumor $normal $outdir/$out/$out $interval 4
    fi
done
