#!/bin/bash

VERSION="1.3"  ## set this by hand


TOPDIR="./ossian-v.${VERSION}"


if [ -e $TOPDIR ] ; then
    echo $TOPDIR exists -- please delete it an try again
    exit 1
fi
if [ -e ./ossian-v.${VERSION}.tgz ] ; then
    echo ./ossian-v.${VERSION}.tgz exists -- please delete it an try again
    exit 1
fi


### -------- build and add html doc -----------
HERE=`pwd`
cd ./doc
gsed "s/__VERSION__/${VERSION}/"  ./source/conf.py.initial > ./source/conf.py
make html
[ $# -ne 0 ] && echo "make doc failed" && exit 1 ;
cd $HERE

mkdir $TOPDIR

### --------- pack and unpack the stuff with tar to preserve all dir structure: ------


tar cf $TOPDIR/ossian_package.tar  \
            ./config_templates/ \
            ./corpus/rm/speakers/rss_toy_demo/ \
            ./corpus/rm/text_corpora/wikipedia_10K_words/ \
            ./corpus/en/speakers/tundra_toy_demo/ \
            ./corpus/en/labelled_corpora/cmudict/cmudict_phones.table \
            ./corpus/en/labelled_corpora/cmudict/letter.names \
            ./corpus/hi/ \
            ./rules/ \
            ./doc/build/ \
            ./example_voices/rm-rss_toy-naive_example.tar \
            ./example_voices/rm-rss_rnd1-naive_example.tar  \
            ./scripts \
            ./test/txt/*.txt \
            ./test/ref_wav/*.wav \
            ./0_README.txt  \
            ./recipes/demo*.cfg  \
            ./recipes/baseline*.cfg  \
            ./recipes/naive*.cfg \
            ./recipes/blizzard_2014_naive*.cfg \
            ./recipes/english_gold_basic.cfg \
            ./tools/patch/*.patch \
            ./tools/downloads \
            ./tools/GlottHMM/
            
cd $TOPDIR
tar xf ossian_package.tar 
rm ossian_package.tar 
cd ..


## ----- add some more directries -----

mkdir -p $TOPDIR/tools/bin
mkdir -p $TOPDIR/tools/downloads


mkdir $TOPDIR/train/
mkdir $TOPDIR/voices/

mkdir $TOPDIR/test/wav

# --- remove any copied junk from release (.pyc and .svn stuff): ----
for FNAME in `find $TOPDIR/* -name *.pyc` ; do
    rm  $FNAME
done

for FNAME in `find $TOPDIR/* | grep .svn` ; do
    rm -rf $FNAME
done

## strip some other mac-crap:
for FNAME in `find $TOPDIR/* -name '.DS_Store'` ; do
    rm  $FNAME
done

# --- remove compiled GlottHMM files, etc.: ----
for FNAME in `find $TOPDIR/tool/GlottHMM/* -name *.o` ; do
    rm  $FNAME
done
rm $TOPDIR/tool/GlottHMM/{Analysis,Synthesis}

### ----- pack up into a tgz file: ----

tar cvzf ./ossian-v.${VERSION}.tgz $TOPDIR
rm -r $TOPDIR




