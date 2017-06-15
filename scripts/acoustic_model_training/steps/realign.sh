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

source $VOICE_BUILD_CONFIG
#----------------------------------------------------------------------



source $UTIL/setup_directory.sh $INDIR $OUTDIR

## copy models:
cp $INDIR/cmp.mmf $OUTDIR/
cp $INDIR/dur.mmf $OUTDIR/

## Copy decision trees if present:
if [ -e $INDIR/tree_dur.txt ] ; then
  cp $INDIR/tree* $OUTDIR
fi








endstate=$[$NSTATE + 1]



mkdir -p $OUTDIR/data/newlab 

$BIN/HSMMAlign -A -C $OUTDIR/config/general.conf -D -V $RELAXED_LABEL_PRUNE -H $INDIR/cmp.mmf -N $INDIR/dur.mmf \
         -I $OUTDIR/data/mlf.full -S $OUTDIR/data/uttlist.cmp -T 1 -t 4000 -w 1.0 \
         -m $OUTDIR/data/newlab $OUTDIR/data/modellist.full $OUTDIR/data/modellist.full
rm -f $OUTDIR/data/newlab_list
find  $OUTDIR/data/newlab/ -name '*.lab' -print > $OUTDIR/data/newlab_list
echo " " > $OUTDIR/null.hed
mv $OUTDIR/data/mlf.full $OUTDIR/data/mlf.full.OLD
$BIN/HLEd -A -D -T 1 -V -l '*' -i $OUTDIR/data/mlf.full -S $OUTDIR/data/newlab_list $OUTDIR/null.hed
