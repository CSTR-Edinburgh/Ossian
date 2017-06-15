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


##!!!!! temp: !!!!!

#SPTK=/Users/owatts/repos/simple4all/CSTRVoiceClone/trunk/bin
#OLDHTS=/Users/owatts/simple4all/hts_on_speed/code/hts2_2/bin  ## ~/repos/simple4all/CSTRVoiceClone/trunk/bin/



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


$TOPDIR/steps/set_up_data.py -labdir $LABDIR -cmpdir $CMPDIR -outdir $OUT/${STEPNUM} -bindir $BIN
check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
                                     
$STEPS/make_monophone.sh $OUT/$PREVIOUS $OUT/$STEPNUM  $BIN
check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]

for j in `seq $NRECLUSTER` ; do

    if [ $j -eq 1 ] ; then
        $STEPS/clone_monophone_to_fullcontext.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
        check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    else
        $STEPS/untie_models.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
        #check_step ; 
        PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    fi
    
    $STEPS/reestimate.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN 0   
    check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
        
    $STEPS/build_MDL_trees.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM 1.0 $QUESTIONS $BIN
    check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]

    for i in `seq $NREEST` ; do
        $STEPS/reestimate.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN 1    
        check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    done
    
    if [ $j -eq 1 ] ; then
        $STEPS/realign.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
        check_step ; PREVIOUS=$STEPNUM ; STEPNUM=$[$STEPNUM + 1]
    fi
    
done



$STEPS/make_engine_model.sh $OUT/$PREVIOUS/ $OUT/$STEPNUM $BIN
check_step

rm -rf $OUT/final_model/
cp -r  $OUT/$STEPNUM/ $OUT/final_model/

end_time=$(date +"%s")
time_diff=$(($end_time-$start_time))

echo "Model training took $(($time_diff / 60)) minutes and $(($time_diff % 60)) seconds to run."
