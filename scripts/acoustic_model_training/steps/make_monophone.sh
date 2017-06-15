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

set -e

source $UTIL/setup_directory.sh $INDIR $OUTDIR




$UTIL/make_proto_hsmm.py $OUTDIR/proto.txt $VOICE_BUILD_CONFIG



## -------- floor variance ---------:
## cmp:
$BIN/HCompV -A -C $OUTDIR/config/general.conf -D -V -S $OUTDIR/data/uttlist.cmp -T 1 -M $OUTDIR $OUTDIR/proto.txt
if [ $? -gt 0 ] ; then echo "Floor variance failed" ;exit 1 ; fi
head -n 1 $OUTDIR/proto.txt | cat - $OUTDIR/vFloors > $OUTDIR/floor_cmp.mmf




## dur -- floor variance to 1.0:
rm -f $OUTDIR/floor_dur.mmf
for i in `seq $NSTATE` ; do
    echo "~v varFloor${i}" >> $OUTDIR/floor_dur.mmf
    echo "<Variance> 1" >> $OUTDIR/floor_dur.mmf
    echo "1.0" >> $OUTDIR/floor_dur.mmf
done


## ------- segmental K-means & EM-based estimation of monophones: ------
mkdir $OUTDIR/hinit
mkdir $OUTDIR/hrest_cmp
mkdir $OUTDIR/hrest_dur
i=1

for phone in `cat $OUTDIR/data/modellist.mono`; do
    echo $phone
    $BIN/HInit -A -C $OUTDIR/config/general.conf -D -V -H $OUTDIR/floor_cmp.mmf \
            -I $OUTDIR/data/mlf.mono -M $OUTDIR/hinit -o $phone -S $OUTDIR/data/uttlist.cmp \
            -T 1 -l $phone -m 1 -u tmvw -w 3 $OUTDIR/proto.txt
    $BIN/HRest -A -C $OUTDIR/config/general.conf -D -V -H $OUTDIR/floor_cmp.mmf \
            -I $OUTDIR/data/mlf.mono -M $OUTDIR/hrest_cmp -o $phone -S $OUTDIR/data/uttlist.cmp \
            -T 1 -l $phone -g $OUTDIR/hrest_dur/$phone -m 1 -u tmvw -w 3 $OUTDIR/hinit/$phone
    mv $OUTDIR/hrest_cmp/$phone $OUTDIR/hrest_cmp/$i-mmf
    mv $OUTDIR/hrest_dur/$phone $OUTDIR/hrest_dur/$i-mmf
    i=$[$i + 1]
    if [ $? -gt 0 ] ; then echo "HInit failed for $phone" ;exit 1 ; fi
done
  

## ------ join individual monophone files together --------
mkdir $OUTDIR/joined_0

## cmp:
echo  "FV $OUTDIR/floor_cmp.mmf" > $OUTDIR/join_cmp.hed   ## make hed file

arg=""
i=1
for phone in `cat $OUTDIR/data/modellist.mono`; do
    arg="$arg -H $OUTDIR/hrest_cmp/$i-mmf"
    i=$[$i + 1]
done

$BIN/HHEd -A -B -C $OUTDIR/config/general.conf -D -V -T 1 $arg -s -p -i -w $OUTDIR/joined_0/cmp.mmf $OUTDIR/join_cmp.hed $OUTDIR/data/modellist.mono


## dur:
echo  "FV $OUTDIR/floor_dur.mmf" > $OUTDIR/join_dur.hed   ## make hed file

arg=""
i=1
for phone in `cat $OUTDIR/data/modellist.mono`; do
    arg="$arg -H $OUTDIR/hrest_dur/$i-mmf"
    i=$[$i + 1]
done

$BIN/HHEd -A -B -C $OUTDIR/config/general.conf -D -V -T 1 $arg -s -p -i -w $OUTDIR/joined_0/dur.mmf $OUTDIR/join_dur.hed $OUTDIR/data/modellist.mono


NREEST=5
## ------ embedded reestimation --------
for new in `seq ${NREEST}` ; do
    old=$[$new - 1]
    mkdir $OUTDIR/joined_${new}
    $BIN/HERest -A -B -C $OUTDIR/config/general.conf -D -V -H $OUTDIR/joined_${old}/cmp.mmf \
         -N $OUTDIR/joined_${old}/dur.mmf -e 2 -I $OUTDIR/data/mlf.mono -M $OUTDIR/joined_${new} \
         -R $OUTDIR/joined_${new} -S $OUTDIR/data/uttlist.cmp -T 1 -m 1 -t 5000 5000 10000 \
         -u mvwtdmv -w 3 $OUTDIR/data/modellist.mono $OUTDIR/data/modellist.mono
done

cp $OUTDIR/joined_${NREEST}/cmp.mmf $OUTDIR/cmp.mmf 
cp $OUTDIR/joined_${NREEST}/dur.mmf $OUTDIR/dur.mmf 


