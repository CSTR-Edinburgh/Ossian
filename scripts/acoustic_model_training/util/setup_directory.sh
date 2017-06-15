#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


#----------------------------------------------------------------------

INDIR=$1
OUTDIR=$2

[ $# -ne 2 ] && echo "Wrong number of arguments supplied" && exit 1 ;

UTIL="$( cd "$( dirname "$0" )/../util" && pwd )"  ## location of util script

#----------------------------------------------------------------------


### Don't overwrite existing data! Allows bigger data etc to be copied in  before this is called.
mkdir -p $OUTDIR/data
for datafile in uttlist.cmp uttlist.lab modellist.mono modellist.full mlf.mono mlf.full ; do
    if [ ! -e $OUTDIR/data/$datafile ] ; then
        cp $INDIR/data/$datafile $OUTDIR/data/$datafile
    fi
done

for optional_file in mlf.words lexicon.txt ; do
    if [ -e $INDIR/data/$optional_file ] ; then
        cp $INDIR/data/$optional_file $OUTDIR/data/$optional_file ;
    fi
done

$UTIL/make_config.sh $OUTDIR/config/
