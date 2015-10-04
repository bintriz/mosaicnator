#!/bin/bash

# for snp in $(ls *.varscan.all.snp); do
#     echo "Processing $snp"
#     java -jar $VARSCAN processSomatic $snp --p-value 0.05
# done

for indel in $(ls data.out/*.varscan/*.indel); do
    echo "Processing $snp"
    java -jar $VARSCAN processSomatic $indel --p-value 0.05
done
