#!/bin/bash


## osw: this script not in use yet.


LANG_CODE=$1


USAGE="Please supply a single language code, from the set: ... "

if [ $# -ne 1 ] ; then
    echo $USAGE ;
    exit 1 ;
fi


URLSTEM="http://tundra.simple4all.org/data"
DIR="$( cd "$( dirname "$0" )" && pwd )"   ## location of this script
CORPUS_OUT=$DIR/corpus/$LANG_CODE/speakers/tundra_v1_1hour/

echo $LANG_CODE

case LANG_CODE in 
    en ) 
        DATA_ARCHIVE=EN_livingalone_1hr.zip
        ;;
    de) 
        DATA_ARCHIVE=DE_doriangray.zip
        ;;
    *) 
        echo $USAGE ; exit 1 ;;
esac 

mkdir -p $CORPUS_OUT




echo "Download Tundra 1 hour subset for language $LANG_CODE..."
HERE=`pwd`
cd $CORPUS_OUT
wget $URLSTEM/$DATA_ARCHIVE
unzip $DATA_ARCHIVE



