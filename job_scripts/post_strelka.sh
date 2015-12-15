#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

datadir=$1
sample=$2

# =======
# strelka
# =======

rm -r $datadir/chromosomes