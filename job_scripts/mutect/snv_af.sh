#!/bin/bash
#$ -q 4-days
#$ -cwd

. ~/.bash_profile > /dev/null

MINMQ=$1
MINBQ=$2
CLONEBAM=$3
TISSUEBAM=$4
DATAFILE=$5
OUTFILE=$6

COORDFILE=${OUTFILE/snv_AF.txt/snv_coord.txt}
DATAMD5=$(dirname $DATAFILE)/checksum/$(basename $DATAFILE).md5
OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5

if [ ! -f $DATAFILE ] || [ ! -f $DATAMD5 ] || \
       [ "$(md5sum $DATAFILE|cut -f1 -d' ')" != "$(cut -f1 -d' ' $DATAMD5)" ]; then
    echo "$DATAFILE doesn't exist or doesn't match to the checksum."
    exit 1
fi

tail -n+3 $DATAFILE \
    |cut -f-2,4-5 \
    |perl -ne '
	my ($chr, $pos, $ref, $alt) = split /\t/;
	chomp($alt);
	grep { print "$chr\t$pos\t$ref\t$_\n" } split /,/, $alt;
    ' > $COORDFILE
snv_af.py -c $CLONEBAM -t $TISSUEBAM -q $MINMQ -Q $MINBQ $COORDFILE > $OUTFILE
rm -rf $COORDFILE

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
