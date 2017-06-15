#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk

#----------------------------------------------------------------------

INDIR=$1
OUTDIR=$2
MDLWEIGHT=$3
QUESTIONS=$4
BIN=$5

[ $# -ne 5 ] && echo "build_MDL_trees.sh: Wrong number of arguments supplied" && exit 1 ;

UTIL="$( cd "$( dirname "$0" )/../util" && pwd )"  ## location of util script

if [ -z $VOICE_BUILD_CONFIG ] ; then
    echo 'Environment variable VOICE_BUILD_CONFIG has not been set!' ; exit 1
fi
source $VOICE_BUILD_CONFIG

#----------------------------------------------------------------------

source $UTIL/setup_directory.sh $INDIR $OUTDIR






endstate=$[$NSTATE + 1]




## Make edit file for building ALL cmp trees:

echo "RO 0 $INDIR/stat.cmp" > $OUTDIR/cluster_cmp.hed 
echo "TR 1"             >> $OUTDIR/cluster_cmp.hed 
cat $QUESTIONS          >> $OUTDIR/cluster_cmp.hed 
echo "TR 1"             >> $OUTDIR/cluster_cmp.hed 
for STREAM in $STREAMS ; do     
    for STATE in `seq 2 $endstate` ; do
        NAME="stream-${STREAM}-state-${STATE}"
        echo "TB 0 ${NAME}_ {*.state[${STATE}].stream[${STREAM}]}" >> $OUTDIR/cluster_cmp.hed 
    done
    #echo "ST $OUTDIR/tree_cmp_str_${STREAM}.txt"  >> $OUTDIR/cluster_cmp.hed 
done
echo "TR 1"             >> $OUTDIR/cluster_cmp.hed 
echo "ST $OUTDIR/tree_cmp.txt"  >> $OUTDIR/cluster_cmp.hed 


$BIN/HHEd -A $BINMOD -C $OUTDIR/config/general.conf -D -T 1  \
         -i -m -a $MDLWEIGHT -H $INDIR/cmp.mmf  \
        -p -r 1 -s -w $OUTDIR/cmp.mmf $OUTDIR/cluster_cmp.hed $OUTDIR/data/modellist.full




## Duration:

echo "RO 0 $INDIR/stat.dur" > $OUTDIR/cluster_dur.hed 
echo "TR 1"             >> $OUTDIR/cluster_dur.hed 
cat $QUESTIONS          >> $OUTDIR/cluster_dur.hed 
echo "TR 1"             >> $OUTDIR/cluster_dur.hed 
echo "TB 0 duration_ {*.state[2].stream[1-${NSTATE}]}" >> $OUTDIR/cluster_dur.hed   
echo "TR 1"             >> $OUTDIR/cluster_dur.hed 
echo "ST $OUTDIR/tree_dur.txt"  >> $OUTDIR/cluster_dur.hed 


$BIN/HHEd -A $BINMOD -C $OUTDIR/config/general.conf -D -T 1  \
         -i -m -a $MDLWEIGHT -H $INDIR/dur.mmf  \
        -p -r 1 -s -w $OUTDIR/dur.mmf $OUTDIR/cluster_dur.hed $OUTDIR/data/modellist.full
        
        
        
        
        

## ------------------------ check success ----------------------------
if [ -z `grep -l QS $OUTDIR/tree_cmp.txt` ] ; then
    echo "Building emission trees failed: no QS lines in $OUTDIR/tree_cmp.txt"
    exit 1
fi
if [ -z `grep -l QS $OUTDIR/tree_dur.txt` ] ; then
    echo "Building duration trees failed: no QS lines in $OUTDIR/tree_dur.txt"
    exit 1
fi
if [ ! -e $OUTDIR/cmp.mmf ] ; then
    echo "Building duration trees failed: no $OUTDIR/cmp.mmf"
    exit 1
fi
if [ ! -e $OUTDIR/dur.mmf ] ; then
    echo "Building duration trees failed: no $OUTDIR/dur.mmf"
    exit 1
fi
## -------------------------------------------------------------------
