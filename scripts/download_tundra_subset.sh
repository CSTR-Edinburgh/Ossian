#!/bin/bash




LANG_CODE=$1


USAGE="Please supply a single language code, from the set: bg, de, en, fi, hu, it, pl "

echo $#

if [ $# -ne 1 ] ; then
    echo $USAGE ;
    exit 1 ;
fi


URLSTEM="http://tundra.simple4all.org/data"
DIR="$( cd "$( dirname "$0" )" && pwd )"   ## location of this script
CORPUS_OUT=$DIR/../corpus/$LANG_CODE/speakers/tundra_v1_1hour/

echo $CORPUS_OUT
echo $LANG_CODE

case $LANG_CODE in 
    bg )
        DATA_ARCHIVE=BG_zhetvariat_1hr.zip
        ;;
    de ) 
        DATA_ARCHIVE=DE_doriangray.zip
        ;;        
    en ) 
        DATA_ARCHIVE=EN_livingalone_1hr.zip
        ;;
    fi )
        DATA_ARCHIVE=FI_rautatie_1hr.zip
        ;;        
    hu )
        DATA_ARCHIVE=HU_egri_1hr.zip
        ;;
    it )
        DATA_ARCHIVE=IT_galatea_1hr.zip
        ;;        
    pl )
        DATA_ARCHIVE=PL_siedem_1hr.zip
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



mv */train/text/ ./txt/
mv */train/wav/ ./wav/



