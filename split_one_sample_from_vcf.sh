#!/bin/bash

[ $# -lt 2 ] && { echo -e "Usage:\n  $(basename "$0") sample.name input.vcf"; exit 1; }

sample=$1
file=$2

bcftools view -c1 -Oz -s $sample -o ${file/.vcf*/.$sample.vcf.gz} $file
