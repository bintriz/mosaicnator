#!/bin/bash

[ $# -lt 5 ] && { echo -e "Usage:\n  $(basename "$0") ref clone.bam tissue.bam snv.coord out.name"; exit 1; }

ref=$1
clone=$2
tissue=$3
snv=$4
out=$5

SCRIPT_PATH=$(dirname $(readlink -f ${BASH_SOURCE[0]}))

qsub $SCRIPT_PATH/get_AF.sh $ref $clone $tissue $snv $out
