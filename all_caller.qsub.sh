#!/bin/bash

[ $# -lt 5 ] && { echo -e "Usage:\n  $(basename "$0") ref.fa clone.bam tissue.bam sample.name out.dir [interval_bed]"; exit 1; }

ref=$1
tumor=$2
normal=$3
sample=$4
outdir=$5
interval_bed=$6

SCRIPT_PATH=$(dirname $(readlink -f ${BASH_SOURCE[0]}))

##
## mutect
##
out=$sample.mutect

if [ "$interval_bed" == "" ]; then
    job_name=mutect.$sample
    echo Submit $out
    qsub -N $job_name -q 1-day $SCRIPT_PATH/mutect.sh $ref $tumor $normal $outdir/$out
else
    q_err=q.err/mutect.$sample
    q_out=q.out/mutect.$sample
    
    if [ ! -d $outdir/$out ]; then
	mkdir -p $outdir/$out
    fi
    if [ ! -d $q_err ]; then
	mkdir -p $q_err
    fi
    if [ ! -d $q_out ]; then
	mkdir -p $q_out
    fi

    for interval in $(awk '{print $1":"$2+1"-"$3 }' $interval_bed); do
	job_name=mutect.$sample.${interval/:/-}
	echo Submit $out $interval
	qsub -N $job_name -q 1-day -o $q_out -e $q_err $SCRIPT_PATH/mutect.sh $ref $tumor $normal $outdir/$out/$out $interval
    done
fi

##
## varscan
##
out=$sample.varscan

if [ "$interval_bed" == "" ]; then
    job_name=varscan.$sample
    echo Submit $out

    if [ ! -d $outdir/$out ]; then
	mkdir -p $outdir/$out
    fi
    
    qsub -N $job_name -q 1-day $SCRIPT_PATH/varscan.sh $ref $tumor $normal $outdir/$out/$out
else
    q_err=q.err/varscan.$sample
    q_out=q.out/varscan.$sample
    
    if [ ! -d $outdir/$out ]; then
	mkdir -p $outdir/$out
    fi
    if [ ! -d $q_err ]; then
	mkdir -p $q_err
    fi
    if [ ! -d $q_out ]; then
	mkdir -p $q_out
    fi

    for interval in $(awk '{print $1":"$2+1"-"$3 }' $interval_bed); do 
	job_name=varscan.$sample.${interval/:/-}
	echo Submit $out $interval
	qsub -N $job_name -q 1-day -o $q_out -e $q_err $SCRIPT_PATH/varscan.sh $ref $tumor $normal $outdir/$out/$out $interval
    done
fi

##
## somaticsniper
##
out=$sample.somaticsniper

job_name=somaticsniper.$sample
echo Submit $out
qsub -N $job_name $SCRIPT_PATH/somaticsniper.sh $ref $tumor $normal $outdir/$out

##
## strelka
##
out=$sample.strelka

job_name=strelka.$sample
echo Submit $out
qsub -N $job_name $SCRIPT_PATH/strelka.sh $ref $tumor $normal $outdir/$out
