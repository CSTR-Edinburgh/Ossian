#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


#----------------------------------------------------------------------

INDIR=$1
OUTDIR=$2
NCOMPONENTS=$3
BIN=$4


[ $# -ne 4 ] && echo "Wrong number of arguments supplied" && exit 1 ;

UTIL="$( cd "$( dirname "$0" )/../util" && pwd )"  ## location of util script

if [ -z $VOICE_BUILD_CONFIG ] ; then
    echo 'Environment variable VOICE_BUILD_CONFIG has not been set!' ; exit 1
fi
source $VOICE_BUILD_CONFIG

#----------------------------------------------------------------------

## no label prune!!!!

source $UTIL/setup_directory.sh $INDIR $OUTDIR

LAST_STATE=$[${NSTATE}+2]

echo "MU $NCOMPONENTS {*.state[2-${LAST_STATE}].stream[${MIXUP_STREAMS}].mix}" > $OUTDIR/mixup.hed

$BIN/HHEd -A $BINMOD -C $OUTDIR/config/general.conf -D -T 1 -H $INDIR/cmp.mmf -M $OUTDIR/ $OUTDIR/mixup.hed $OUTDIR/data/modellist.mono 
     
## ------------------------ check success ----------------------------
if [ ! -e $OUTDIR/cmp.mmf ] ; then
    echo "Reestimation failed: cmp.mmf not made"
    exit 1
fi
## -------------------------------------------------------------------


