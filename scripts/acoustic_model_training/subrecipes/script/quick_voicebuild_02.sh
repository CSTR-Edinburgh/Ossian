#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk

#----------------------------------------------------------------------

CMPDIR=$1
LABDIR=$2
QUESTIONS=$3
BIN=$4
OUT=$5
CONFIG=$6

[ $# -ne 6 ] && echo "Wrong number of arguments supplied" && exit 1 ;

## location of directory 2 above that the script is in:
TOPDIR="$( cd "$( dirname "$0" )"/../../ && pwd )"

#----------------------------------------------------------------------

## defaults for configured values:
MONOPHONE_SUBSET="1examples"
SUBSETS="5minutes 10minutes 20minutes all"
SHORT_QUESTION_PATT="segment_is"

#----------------------------------------------------------------------




export VOICE_BUILD_CONFIG=$CONFIG

source $VOICE_BUILD_CONFIG


STEPS=$TOPDIR/steps/
UTIL=$TOPDIR/util/

function check_step {
    ## use global $? and $STEPNUM
    if [ $? -gt 0 ] ; then 
        echo ; echo "Step ${STEPNUM} in script $0 failed, aborted!" ; echo ; exit 1 ; 
    fi
}





start_time=$(date +"%s")





## prepare SHORT_QUESTIONS:
mkdir -p $OUT/
SHORT_QUESTIONS=$OUT/short_questions.hed
grep $SHORT_QUESTION_PATT $QUESTIONS > $SHORT_QUESTIONS




STEPNUM=1                 

## Make small data set for training monophone models:
$TOPDIR/steps/set_up_data.py -labdir $LABDIR -cmpdir $CMPDIR -outdir $OUT/data_${MONOPHONE_SUBSET} \
            -bindir $BIN -subset $MONOPHONE_SUBSET
                           
$STEPS/make_monophone.sh $OUT/data_${MONOPHONE_SUBSET} $OUT/$STEPNUM  $BIN
check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]


FIRST_ITER=1
for SUBSET in $SUBSETS ; do

    ## Move up to more data -- make it in $OUT/$STEPNUM where future models are trained:
    $TOPDIR/steps/set_up_data.py -labdir $LABDIR -cmpdir $CMPDIR -outdir $OUT/$STEPNUM \
            -bindir $BIN -subset $SUBSET
    check_step ;

    if [ $FIRST_ITER -eq 1 ] ; then
        $STEPS/clone_monophone_to_fullcontext.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
        check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    else
        $STEPS/untie_models.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
        #check_step ;   ### this gave fail even when ran ok...
        PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    fi
    
    $STEPS/reestimate.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN 0   
    check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
        
    QUESTIONS_TO_USE=$SHORT_QUESTIONS
    if [ $SUBSET == "all" ] ; then
        QUESTIONS_TO_USE=$QUESTIONS
    fi    
    
    echo "$STEPS/build_MDL_trees.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM 1.0 $QUESTIONS_TO_USE $BIN"    
    $STEPS/build_MDL_trees.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM 1.0 $QUESTIONS_TO_USE $BIN
    check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    
    for i in `seq $NREEST` ; do
        $STEPS/reestimate.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN 1    
        check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    done
    
#     if [ $FIRST_ITER -eq 1 ] ; then
#         $STEPS/realign.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
#         check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
#     fi
    FIRST_ITER=0
done

$STEPS/make_engine_model.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
check_step

rm -rf $OUT/final_model/
cp -r  $OUT/$STEPNUM/ $OUT/final_model/

end_time=$(date +"%s")
time_diff=$(($end_time-$start_time))

echo "Model training took $(($time_diff / 60)) minutes and $(($time_diff % 60)) seconds to run."
