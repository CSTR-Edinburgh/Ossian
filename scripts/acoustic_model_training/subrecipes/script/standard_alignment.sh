#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk

#----------------------------------------------------------------------

CMPDIR=$1
LABDIR=$2
BIN=$3
OUT=$4
CONFIG=$5

[ $# -ne 5 ] && echo "Wrong number of arguments supplied" && exit 1 ;

## location of directory 2 above that the script is in:
TOPDIR="$( cd "$( dirname "$0" )"/../../ && pwd )"

#----------------------------------------------------------------------

export VOICE_BUILD_CONFIG=$CONFIG

source $VOICE_BUILD_CONFIG


STEPS=$TOPDIR/steps/

function check_step {
    ## use global $? and $STEPNUM
    if [ $? -gt 0 ] ; then 
        echo ; echo "Step ${STEPNUM} in script $0 failed, aborted!" ; echo ; exit 1 ; 
    fi
}


STEPNUM=1 

start_time=$(date +"%s")

## ------ preparation ------

python $STEPS/set_up_data.py -labdir $LABDIR -cmpdir $CMPDIR -outdir $OUT/${STEPNUM} -bindir $BIN
check_step ;
$STEPS/make_alignment_lexicon.sh $OUT/$STEPNUM  $BIN
check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]

$STEPS/make_alignment_monophone.sh $OUT/$PREVIOUS $OUT/$STEPNUM  $BIN
check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]


## ------ training -----

for NMIX in $MIXTURE_SCHEDULE ; do
    echo "$NMIX ==== "
    if [ ! $NMIX == 0 ] ; then
        $STEPS/increase_mixture_components.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $NMIX $BIN
        check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    fi
    ## --- reestimation ---
    for i in `seq $NREEST` ; do
         $STEPS/reestimate_alignment_model.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
         check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    done
    ## --- realignment ---
    $STEPS/realign_to_labels.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
    check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
done

rm -rf $OUT/final_model/
cp -r  $OUT/$PREVIOUS/ $OUT/final_model/

end_time=$(date +"%s")
time_diff=$(($end_time-$start_time))

echo "Aligner training took $(($time_diff / 60)) minutes and $(($time_diff % 60)) seconds to run."


