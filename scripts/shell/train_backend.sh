#!/bin/bash

## Script to run other scripts to train HTS back-end using STRAIGHT features.
## In the near future, feature extraction and synthesis model building
## will also be handled inside the train.py script, at which point this script will
## no longer need to exist ;-)




LNG=$1
SPEAKER=$2
RECIPE=$3
VCDIR=$4      ## location of S4A VCTK (e.g. <SOME_PATH>/simple4all/CSTRVoiceClone/ )

echo $VCDIR

## location of script:
ROOT="$( cd "$( dirname "$0" )" && pwd )" 

## derived paths:
NAIVE_DIR=$ROOT/../../  ## parent of config, script, etc.
VOICE_DIR=$NAIVE_DIR/train/$LNG/speakers/$SPEAKER/$RECIPE/  ## location of the voice being trained 
WAV_DIR=$NAIVE_DIR/corpus/$LNG/speakers/$SPEAKER/wav/   ##



## Make paths absolute:
VOICE_DIR=`greadlink -fn $VOICE_DIR`
WAV_DIR=`greadlink -fn $WAV_DIR`
NAIVE_DIR=`greadlink -fn $NAIVE_DIR`
VCDIR=`greadlink -fn $VCDIR`

echo "Voice dir: ${VOICE_DIR}"
echo "Wav dir: ${WAV_DIR}"
echo "Naive dir: ${NAIVE_DIR}"
echo "VC dir dir: ${VCDIR}"



## make a place to put synth training features:
FEATURE_DIR=$VOICE_DIR/synth_feats
mkdir $FEATURE_DIR


## make a place to put synth model:
SYNTH_DIR=$VOICE_DIR/processors/acoustic_model/
if [ ! -e $SYNTH_DIR ] ; then
  echo "$SYNTH_DIR does not exist!" ; 
  exit 1 ;
fi


## =============================
## 1) extract STRAIGHT features:

## Get template config file:
STRAIGHT_CONF=$FEATURE_DIR/straight_config.txt
echo $NAIVE_DIR/
cp $NAIVE_DIR/recipes/straight_config_template.txt $STRAIGHT_CONF

## Make some substitutions in the config file (this should really be done with 
## proper string interpolation in config):

echo $STRAIGHT_CONF 

sed "s@VCDIR@${VCDIR}@" $STRAIGHT_CONF > ${STRAIGHT_CONF}_1
sed "s@FEATDIR@${FEATURE_DIR}@" ${STRAIGHT_CONF}_1 > ${STRAIGHT_CONF}_2
sed "s@ESTDIR@${ESTDIR}@" ${STRAIGHT_CONF}_2 > ${STRAIGHT_CONF}_3
sed "s@WAVDIR@${WAV_DIR}@" ${STRAIGHT_CONF}_3 > ${STRAIGHT_CONF}_4

mv ${STRAIGHT_CONF}_4  ${STRAIGHT_CONF}

## Use the config to do feature extraction:
HERE=`pwd`
cd $VCDIR/trunk/Research-Demo/fa-tts/STRAIGHT-TTS/
./fa-tts.sh $STRAIGHT_CONF
cd $HERE



## =============================
## 2) make training lists:


## Make training lists, exluding utts for which there are not both cmp and lab files:
echo "$NAIVE_DIR/scripts/util//make_hts_training_lists.sh $FEATURE_DIR/cmp $VOICE_DIR/lab/  $SYNTH_DIR/training_list"
$NAIVE_DIR/scripts/util//make_hts_training_lists.sh $FEATURE_DIR/cmp $VOICE_DIR/lab/  $SYNTH_DIR/training_list



## =============================
## 3) train voice on a single machine:

HERE=`pwd`
cd $VCDIR/trunk/HMM-Training/  

## In the script HTS2011-Training.pl, fix this variable to match the first sentence-level 
## (typically 3rd from last) feature in the labels produced:

## SENTENCE_LEVEL_DELIMITER=/51:  
                                      
## I added ./run-hts2011_general.sh to the repository -- as the name says, it's
## a more general version of the VCTK script -- more things are specified on
## command line so it is less geared to the specifics of VCTK directory structure. 
##

echo "Train HTS model, output log to $SYNTH_DIR/train_log.txt..."

./run-hts2011_general.sh \
    -feature_list $SYNTH_DIR/training_list.cmp \
    -label_list  $SYNTH_DIR/training_list.lab \
    -question_file $VOICE_DIR/questions.hed \
    -out $SYNTH_DIR/ \
      | tee $SYNTH_DIR/train_log.txt

cd $HERE

### copy GV and window parameters for use in synthesis later:
cp $FEATURE_DIR/gv/*   $SYNTH_DIR/hmm/hts_engine/




