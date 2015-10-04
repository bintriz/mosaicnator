#!/bin/bash

[ $# -lt 3 ] && { echo -e "Usage:\n  $(basename "$0") clone.bam tissue.bam sample.name out.dir"; exit 1; }

tumor=$1
normal=$2
sample=$3
outdir=$4
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
    
    if [[ $size -gt 200000000 ]]; then
	qsub -N $job_name -q lg-mem -o $q_out -e $q_err -pe threaded 34 -l h_vmem=8G \
	     $SCRIPT_PATH/scalpel.sh $tumor $normal $outdir/$out/$out $interval 34
    elif [[ $size -gt 100000000 ]]; then
	qsub -N $job_name -q 4-days -o $q_out -e $q_err -pe threaded 25 -l h_vmem=8G \
	     $SCRIPT_PATH/scalpel.sh $tumor $normal $outdir/$out/$out $interval 25
    elif [[ $size -gt 10000000 ]]; then
	qsub -N $job_name -q 4-days -o $q_out -e $q_err -pe threaded 20 -l h_vmem=4G \
	     $SCRIPT_PATH/scalpel.sh $tumor $normal $outdir/$out/$out $interval 20	
    else
	qsub -N $job_name -q 4-days -o $q_out -e $q_err -pe threaded 2 -l h_vmem=4G  \
	     $SCRIPT_PATH/scalpel.sh $tumor $normal $outdir/$out/$out $interval 2
    fi
done
