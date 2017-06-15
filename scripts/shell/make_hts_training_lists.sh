#!/bin/bash

cmp_dir=$1
lab_dir=$2
outfile_stem=$3


lab_out=$outfile_stem.lab
cmp_out=$outfile_stem.cmp

rm $lab_out $cmp_out

for file in $lab_dir/* ; do
	base=`basename $file .lab` ; 
	cmpfile=$cmp_dir/$base.cmp ;
	if [ -e $cmpfile ] ; then
		echo $cmpfile >> $cmp_out ;
		echo $file >> $lab_out ;
	fi
done	
