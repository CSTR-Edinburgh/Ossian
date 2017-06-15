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

## Use grep to get number of last stream from $STREAMS (which looks like e.g. "1 2-4"):
LAST_STREAM=`grep -E -o "[0-9]+" <<<$STREAMS | tail -1`




endstate=$[$NSTATE + 1]



## cmp

echo "LT $INDIR/tree_cmp.txt"                    > $OUTDIR/untie_cmp.hed 
echo "AU $OUTDIR/data/modellist.full"           >> $OUTDIR/untie_cmp.hed 

echo "UT {*.state[2-$endstate].stream[1-$LAST_STREAM]}"    >> $OUTDIR/untie_cmp.hed 
echo "UT {*.state[2-$endstate] }"               >> $OUTDIR/untie_cmp.hed 
echo "TI \"SWeight\" { *.state[2-$endstate].weights }"  >> $OUTDIR/untie_cmp.hed  
echo "UT {*.transP}"                            >>   $OUTDIR/untie_cmp.hed
echo "TI TrP {*.transP}"                        >>   $OUTDIR/untie_cmp.hed

$BIN/HHEd -A $BINMOD -C $OUTDIR/config/general.conf -D -V -T 1 -H $INDIR/cmp.mmf -s -p -i -w $OUTDIR/cmp.mmf $OUTDIR/untie_cmp.hed $INDIR/data/modellist.full
#
[ $? -gt 0 ] && echo "HHEd untie cmp failed" && exit 1 ; 

           
       
       
       
## dur       

echo "LT $INDIR/tree_dur.txt"                    > $OUTDIR/untie_dur.hed 
echo "AU $OUTDIR/data/modellist.full"           >> $OUTDIR/untie_dur.hed 

echo "UT {*.state[2].stream[1-${NSTATE}] }"     >> $OUTDIR/untie_dur.hed 
echo "UT {*.state[2] }"                         >> $OUTDIR/untie_dur.hed 
echo "UT {*.transP}"                            >>   $OUTDIR/untie_dur.hed
echo "TI TrP {*.transP}"                        >>   $OUTDIR/untie_dur.hed

$BIN/HHEd -A $BINMOD -C $OUTDIR/config/general.conf -D -V -T 1 -H $INDIR/dur.mmf -s -p -i -w $OUTDIR/dur.mmf $OUTDIR/untie_dur.hed $INDIR/data/modellist.full
#
[ $? -gt 0 ] && echo "HHEd untie dur failed" && exit 1 ; 





