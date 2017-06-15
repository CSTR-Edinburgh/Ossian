#!/bin/bash

## ./make_hts_training_lists.sh <LAB_DIR> <CMP_DIR> <LIST_NAME>
##
## Look for .lab files in <LAB_DIR> and .cmp files in <CMP_DIR>.
## List them with full pathnames in <LIST_NAME>.lab and <LIST_NAME>.cmp
##

cmp_dir=$1
lab_dir=$2
outfile_stem=$3


lab_out=$outfile_stem.lab
cmp_out=$outfile_stem.cmp


if [ -e $lab_out ] ; then
    rm $lab_out 
fi

if [ -e $cmp_out ] ; then
    rm $cmp_out 
fi


for file in $lab_dir/* ; do
	base=`basename $file .lab` ; 
	cmpfile=$cmp_dir/$base.cmp ;
	if [ -e $cmpfile ] ; then
		echo $cmpfile >> $cmp_out ;
		echo $file >> $lab_out ;
	fi
done	

