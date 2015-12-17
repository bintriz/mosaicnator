#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

DATADIR=$1
SAMPLE=$2

# =======
# strelka
# =======

rm -r $DATADIR/chromosomes
