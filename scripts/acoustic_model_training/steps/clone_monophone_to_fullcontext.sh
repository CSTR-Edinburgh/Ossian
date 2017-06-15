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

source $UTIL/setup_directory.sh $INDIR $OUTDIR




## hardcoded: TODO
NSTATE=5
BINMOD=""



endstate=$[$NSTATE + 1]


## cmp
echo "TI \"SWeight\" { *.state[2-${endstate}].weights }"     >  $OUTDIR/clone_cmp.hed
echo "MM \"trP\"    { *.transP }"                           >>  $OUTDIR/clone_cmp.hed
echo "CL \"$OUTDIR/data/modellist.full\""                   >>  $OUTDIR/clone_cmp.hed

$BIN/HHEd -A $BINMOD -C $OUTDIR/config/general.conf -D -V -T 1 -H $INDIR/cmp.mmf -s -p -i -w $OUTDIR/cmp.mmf $OUTDIR/clone_cmp.hed $INDIR/data/modellist.mono
           
      
## dur     
echo "MM \"trP\"    { *.transP }"                            >  $OUTDIR/clone_dur.hed
echo "CL \"$OUTDIR/data/modellist.full\""                   >>  $OUTDIR/clone_dur.hed

$BIN/HHEd -A $BINMOD -C $OUTDIR/config/general.conf -D -V -T 1 -H $INDIR/dur.mmf -s -p -i -w $OUTDIR/dur.mmf $OUTDIR/clone_dur.hed $INDIR/data/modellist.mono