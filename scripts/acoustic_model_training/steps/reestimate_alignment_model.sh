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

#-----------
# Hard coded:
ALIGN_BEAM=" -t 250.0 500.0 1000.0 "
#-----------


## no label prune!!!!

source $UTIL/setup_directory.sh $INDIR $OUTDIR

## strip skip models from input MLF as an easy way to avoid 'ERROR [+7332]  CreateInsts: Cannot have successive Tee models'
grep -v skip $OUTDIR/data/mlf.mono > $OUTDIR/data/mlf.mono.noskip

$BIN/HERest -A $BINMOD -C $OUTDIR/config/general.conf -D -V -T 1 -S $OUTDIR/data/uttlist.cmp \
         -I $OUTDIR/data/mlf.mono.noskip -m 1 -u tmvw $LABEL_PRUNE $ALIGN_BEAM \
         -H $INDIR/cmp.mmf -M $OUTDIR/ $OUTDIR/data/modellist.mono 


## ------------------------ check success ----------------------------
sleep 1
if [ ! -e $OUTDIR/cmp.mmf ] ; then
    echo "Reestimation failed: cmp.mmf not made"
    exit 1
fi
## -------------------------------------------------------------------


