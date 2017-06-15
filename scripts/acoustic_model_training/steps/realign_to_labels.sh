#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


#----------------------------------------------------------------------

INDIR=$1
OUTDIR=$2
BIN=$3


[ $# -ne 3 ] && echo "Wrong number of arguments supplied" && exit 1 ;

UTIL="$( cd "$( dirname "$0" )/../util" && pwd )"  ## location of util script

if [ -z $VOICE_BUILD_CONFIG ] ; then
    echo 'Environment variable VOICE_BUILD_CONFIG has not been set!' ; exit 1
fi
source $VOICE_BUILD_CONFIG

#----------------------------------------------------------------------


#-------------
# Hard coded:
HVITE_BEAM=" 1000 100000 1000000 "
#-------------


## no label prune!!!!

source $UTIL/setup_directory.sh $INDIR $OUTDIR


$BIN/HVite -l \* -A -C $OUTDIR/config/general.conf -D -V -T 1 -a -m -I $OUTDIR/data/mlf.words \
     -H $INDIR/cmp.mmf -i $OUTDIR/data/mlf.mono.NEW -o SW  \
     -t $HVITE_BEAM -S $OUTDIR/data/uttlist.cmp -y lab $OUTDIR/data/lexicon.txt \
    $INDIR/data/modellist.mono 
if [ $? -gt 0 ] ; then echo "Alignment failed" ; exit 1 ; fi

## ------------------------ check success ----------------------------
if [ ! -e $OUTDIR/data/mlf.mono.NEW ] ; then
    echo "Alignment failed: cmp.mmf not made"
    exit 1
fi
## -------------------------------------------------------------------


## rename new alignment so it will be used in future:
mv $OUTDIR/data/mlf.mono.NEW $OUTDIR/data/mlf.mono

## remove names of utts for which no label has been found from training list:
$UTIL/update_train_list.py -mlf $OUTDIR/data/mlf.mono -trainlist $OUTDIR/data/uttlist.cmp 

## copy models (which weren't updated):
cp $INDIR/cmp.mmf $OUTDIR/cmp.mmf



