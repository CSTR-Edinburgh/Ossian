#!/bin/bash
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


#----------------------------------------------------------------------

INDIR=$1
BIN=$2

[ $# -ne 2 ] && echo "Wrong number of arguments supplied" && exit 1 ;

UTIL="$( cd "$( dirname "$0" )/../util" && pwd )"  ## location of util script

if [ -z $VOICE_BUILD_CONFIG ] ; then
    echo 'Environment variable VOICE_BUILD_CONFIG has not been set!' ; exit 1
fi
source $VOICE_BUILD_CONFIG

#----------------------------------------------------------------------

if [ ! -e $INDIR/data/modellist.mono ] ; then
    echo "$INDIR/data/modellist.mono doesn't exist" ; exit 1 ;
fi

echo "" > $INDIR/data/lexicon.txt  ## clear existing lexicon data
echo "" > $INDIR/data/lexicon.tmp

if [ ! -z $EXTRA_SUBSTITUTIONS ] ; then
    cat $EXTRA_SUBSTITUTIONS >  $INDIR/data/lexicon.txt 
fi


for MODELNAME in `cat $INDIR/data/modellist.mono | sort ` ; do
    case $MODELNAME in
        _SPACE_ ) 
            ## Note the order of skip and sil -- the first provides initial 
            ## expansion; after models are initialised like this, both options 
            ## are allowed. 
            echo '_SPACE_ skip' >> $INDIR/data/lexicon.tmp
            echo '_SPACE_ sil'  >> $INDIR/data/lexicon.tmp
            ;;
        _PUNC_ )
            echo '_PUNC_ sil'   >> $INDIR/data/lexicon.tmp
            echo '_PUNC_ skip'  >> $INDIR/data/lexicon.tmp          
            ;;
        * )
            echo "$MODELNAME $MODELNAME" >> $INDIR/data/lexicon.tmp ;;
    esac
done

for ENTRY in `awk '{print $1}' $INDIR/data/lexicon.txt` ; do
    grep -v "^$ENTRY " $INDIR/data/lexicon.tmp > $INDIR/data/lexicon.tmp2
    mv $INDIR/data/lexicon.tmp2 $INDIR/data/lexicon.tmp
done

cat $INDIR/data/lexicon.tmp >> $INDIR/data/lexicon.txt
rm $INDIR/data/lexicon.tmp


#--------- initial expansion of labels using this lexicon -------------
cp $INDIR/data/mlf.full $INDIR/data/mlf.words

echo "EX" > $INDIR/expand_labels.hed

$BIN/HLEd -I $INDIR/data/mlf.words -i $INDIR/data/mlf.mono -l '*' -d $INDIR/data/lexicon.txt $INDIR/expand_labels.hed $INDIR/data/mlf.words

#--------- re-make monophone list (to add e.g. skip) ------------------
awk '{print $2}' $INDIR/data/lexicon.txt | sort -u > $INDIR/data/modellist.mono
