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



$UTIL/make_proto_hsmm.py $OUTDIR/proto.txt $VOICE_BUILD_CONFIG
$UTIL/make_proto_skip_hsmm.py $OUTDIR/proto_skip.txt $VOICE_BUILD_CONFIG




echo "Floor variance..."
$BIN/HCompV -A -C $OUTDIR/config/general.conf -D -V -f 0.01 -m -S $OUTDIR/data/uttlist.cmp -T 1 -M $OUTDIR $OUTDIR/proto.txt
if [ $? -gt 0 ] ; then echo "Floor variance failed" ; exit 1 ; fi



echo "Generate models..."
mkdir -p $OUTDIR/hcompv/
for m in `cat $OUTDIR/data/modellist.mono` ; do
    echo "phone $m"
    if [ "$m" != "skip" ] ; then  
	    grep -v "~h" $OUTDIR/proto > $OUTDIR/hcompv/$m
    else 
	    cp $OUTDIR/proto_skip.txt $OUTDIR/hcompv/$m            # null topol for skip
    fi
done
echo "models made OK"

echo "Combine models into single file..."
echo " " > $OUTDIR/null.hed 
$BIN/HHEd -d $OUTDIR/hcompv/ -w $OUTDIR/cmp.mmf $OUTDIR/null.hed $OUTDIR/data/modellist.mono
if [ $? -gt 0 ] ; then echo "Model combination failed" ; exit 1 ; fi




