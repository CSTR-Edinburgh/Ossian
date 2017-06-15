#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


#----------------------------------------------------------------------

INDIR=$1
OUTDIR=$2
BIN=$3
FLOOR=$4

[ $# -ne 4 ] && echo "Wrong number of arguments supplied" && exit 1 ;

UTIL="$( cd "$( dirname "$0" )/../util" && pwd )"  ## location of util script

if [ -z $VOICE_BUILD_CONFIG ] ; then
    echo 'Environment variable VOICE_BUILD_CONFIG has not been set!' ; exit 1
fi
source $VOICE_BUILD_CONFIG

#----------------------------------------------------------------------


source $UTIL/setup_directory.sh $INDIR $OUTDIR




## FLOOR=0 is used to perturb untied models before clustering, 1 used for clustered training. 
if [ $FLOOR == 0 ] ; then 
    OPT=" -C $OUTDIR/config/general-unfloor.conf -w 0.0 "  # -w: set mix weight floor to f*MINMIX
else
    OPT=" -C $OUTDIR/config/general.conf -w 3.0 "
fi

$BIN/HERest -A $BINMOD -D -T 1 -S $OUTDIR/data/uttlist.cmp \
         -I $OUTDIR/data/mlf.full -m 1 -u tmvwdmv -t $BEAM \
         -H $INDIR/cmp.mmf -N $INDIR/dur.mmf \
         -M $OUTDIR/ -R $OUTDIR/ \
         $OPT -s $OUTDIR/stat.cmp $STRICT_LABEL_PRUNE \
         $OUTDIR/data/modellist.full $OUTDIR/data/modellist.full

## Make duration stats file: 
awk '{print $1 " " $2 " " $3 " " $3 }' $OUTDIR/stat.cmp > $OUTDIR/stat.dur

## Copy decision trees if present:
if [ -e $INDIR/tree_dur.txt ] ; then
  cp $INDIR/tree* $OUTDIR
fi


## ------------------------ check success ----------------------------
if [ ! -e $OUTDIR/cmp.mmf ] ; then
    echo "Reestimation failed: cmp.mmf not made"
    exit 1
fi
if [ ! -e $OUTDIR/dur.mmf ] ; then
    echo "Reestimation failed: dur.mmf not made"
    exit 1
fi
## -------------------------------------------------------------------


