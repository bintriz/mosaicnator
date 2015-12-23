#!/bin/bash
#$ -q 1-day
#$ -cwd
#$ -l h_vmem=12G

. ~/.bash_profile > /dev/null
plenv shell 5.22.0

REF=$1
CLONEBAM=$2
TISSUEBAM=$3
COORDFILE=$4
OUTFILE=$5
COORDMD5=$(dirname $COORDFILE)/checksum/$(basename $COORDFILE).md5
OUTMD5=$(dirname $OUTFILE)/checksum/$(basename $OUTFILE).md5

if [ ! -f $COORDFILE ] || [ ! -f $COORDMD5 ] || \
       [ "$(md5sum $COORDFILE)" != "$(cat $COORDMD5)" ]; then
    echo "$COORDFILE doesn't exist or doesn't match to the checksum."
    exit 1
fi

get_AF.pl -r $REF -c $CLONEBAM -t $TISSUEBAM -s $COORDFILE > $OUTFILE

mkdir -p $(dirname $OUTMD5)
md5sum $OUTFILE > $OUTMD5
rm -rf $COORDFILE $COORDMD5
