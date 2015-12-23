#!/bin/bash
#$ -q 1-day
#$ -cwd

. ~/.bash_profile > /dev/null

DATAFILE=$1
OUTFILE=$2
DATAMD5=$(dirname $DATAFILE)/checksum/$(basename $DATAFILE).md5
OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5

if [ ! -f $DATAFILE ] || [ ! -f $DATAMD5 ] || \
       [ "$(md5sum $DATAFILE)" != "$(cat $DATAMD5)" ]; then
    echo "$DATAFILE doesn't exist or doesn't match to the checksum."
    exit 1
fi

grep -v '^#' $DATAFILE \
    |cut -f-2,4-5 \
    |perl -ne '
	my ($chr, $pos, $ref, $alt) = split /\t/;
	chomp($alt);
	grep { print "$chr\t$pos\t$ref\t$_\n" } split /,/, $alt;
    ' > $OUTFILE

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
