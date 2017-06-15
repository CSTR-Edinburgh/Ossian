#!/bin/bash

## This is a script which basically runs commands in the documentation to set up tools and build a few voices on toy data sets. For now it is meant for internal use rather than release.




## Control what to test here:
# CHECK_PYTHON=1
SETUP=0
NAIVE=0
TOPLINE=1





## OSSIAN is the location of script:
OSSIAN="$( cd "$( dirname "$0" )" && pwd )" 







## Still to do: check python installation:
# command -v pip-2.7 >/dev/null 2>&1 || { echo >&2 "I require pip-2.7 but it's not installed.  Aborting."; exit 1; }
# 
# 
# python -c "import numpy; print numpy.__version__"
# pip-2.7 freeze




## Installation
if [ $SETUP == 1 ] ; then


    : ${HTK_USERNAME?"Need to set HTK_USERNAME with export"}
    : ${HTK_PASSWORD?"Need to set HTK_PASSWORD with export"}

    ## clean existing binaries:
    rm -rf $OSSIAN/tools/bin/*
    rm -rf $OSSIAN/tools/GlottHMM/{Analysis,Synthesis}


    ## Assuming that you want to compile everything cleanly from scratch:
    rm -r $OSSIAN/tools/downloads/*
    rm -r $OSSIAN/tools/bin/*

    ## Make sure these locations exist:
    mkdir -p $OSSIAN/tools/bin
    mkdir -p $OSSIAN/tools/downloads

    cd $OSSIAN/tools/downloads

    ## Download HTK source code:
    wget http://htk.eng.cam.ac.uk/ftp/software/HTK-3.4.1.tar.gz --http-user=$HTK_USERNAME --http-password=$HTK_PASSWORD
    wget http://htk.eng.cam.ac.uk/ftp/software/hdecode/HDecode-3.4.1.tar.gz  --http-user=$HTK_USERNAME --http-password=$HTK_PASSWORD

    ## Download HTS patch:
    wget http://hts.sp.nitech.ac.jp/archives/2.3alpha/HTS-2.3alpha_for_HTK-3.4.1.tar.bz2

    ## Unpack everything:
    tar -zxvf HTK-3.4.1.tar.gz
    tar -zxvf HDecode-3.4.1.tar.gz
    tar -xvf HTS-2.3alpha_for_HTK-3.4.1.tar.bz2

    ## Apply HTS patch:
    cd htk
    patch -p1 -d . < ../HTS-2.3alpha_for_HTK-3.4.1.patch


    ## Apply the Ossian patch:
    patch -p1 -d . < ../../patch/ossian_hts.patch

    ## Finally, configure and compile:
    ./configure --prefix=$OSSIAN/tools/ --without-x --disable-hslab
    make
    make install

    ## Get hts_engine:
    cd $OSSIAN/tools/downloads
    wget http://sourceforge.net/projects/hts-engine/files/hts_engine%20API/hts_engine_API-1.05/hts_engine_API-1.05.tar.gz
    tar xvf hts_engine_API-1.05.tar.gz
    cd hts_engine_API-1.05
    ## Patch engine for use with Ossian (glottHMM compatibility):
    patch -p1 -d . < ../../patch/ossian_engine.patch
    ./configure --prefix=$OSSIAN/tools/
    make
    make install

    ## Get SPTK:
    cd $OSSIAN/tools/downloads
    wget http://downloads.sourceforge.net/sp-tk/SPTK-3.6.tar.gz
    tar xvf SPTK-3.6.tar.gz
    cd SPTK-3.6
    ./configure --prefix=$OSSIAN/tools/

    ## To compile on Mac, modify Makefile for delta tool:
    mv ./bin/delta/Makefile ./bin/delta/Makefile.BAK
    sed 's/CC = gcc/CC = clang/' ./bin/delta/Makefile.BAK > ./bin/delta/Makefile     ## (see http://sourceforge.net/p/sp-tk/bugs/68/)

    make
    make install

    ## Count the binaries in your bin directory:
    ls $OSSIAN/tools/bin/* | wc -l
    ## If all the tools have been compiled OK, you should have 160 or 163 of them.


    ## Glott HMM
    cd $OSSIAN/tools/GlottHMM/
    make

fi


if [ $NAIVE == 1 ] ; then

    ### TRAIN ON TOY DATASETS AND SYNTHESISE WITH 4 RECIPES:- 

    ## clean previously trained voices and training files:
    rm -rf ./train/{rm,en,hi}/speakers/*/*/ ./voices/{rm,en,hi}/*/*/

    ## clean previous synthesis:
    rm -rf ./test/wav/*


    # naive
    python ./scripts/train.py -s rss_toy_demo -l rm -text wikipedia_10K_words naive

    ./scripts/speak.py -l rm -s rss_toy_demo -o ./test/wav/romanian_toy_naive.wav naive ./test/txt/romanian.txt


    # naive_glott
    python ./scripts/train.py -s rss_toy_demo -l rm -text wikipedia_10K_words naive_glott

    ./scripts/speak.py -l rm -s rss_toy_demo -o ./test/wav/romanian_toy_naive_glott.wav \
                                            naive_glott ./test/txt/romanian.txt


    # naive_glott_prom
    python ./scripts/train.py -s rss_toy_demo -l rm -text wikipedia_10K_words naive_glott_prom

    ./scripts/speak.py -l rm -s rss_toy_demo -o ./test/wav/romanian_toy_naive_glott_prom.wav \
                                             naive_glott_prom ./test/txt/romanian.txt

    # blizzard_2014_naive_latinised_glott
    python ./scripts/train.py -s toy -l hi -text wikipedia_10K_words blizzard_2014_naive_latinised_glott

    ./scripts/speak.py -l hi -s toy -o ./test/wav/hindi_naive_latinised_glott.wav \
                                 blizzard_2014_naive_latinised_glott ./test/txt/hindi.txt

fi


if [ $TOPLINE == 1 ] ; then

    ### INSTALL EXTRA DEPENDENCIES FOR ENGLISH GOLD:-

    ## clean up:
    rm -rf $OSSIAN/tools/corenlp-python/  $OSSIAN/tools/g2p/  \
        $OSSIAN/tools/downloads/* $OSSIAN/corpus/en/labelled_corpora/cmudict/cmudict-0.4.out 



    # Stanford core NLP with Python bindings

    cd $OSSIAN//tools

    ## Get the Python bindings (we assume git is installed):
    git clone https://bitbucket.org/torotoki/corenlp-python.git

    ## Make a small alteration to the bindings:
    mv ./corenlp-python/corenlp/corenlp.py ./corenlp-python/corenlp/corenlp.py.BAK
    sed 's/?.?.?-models/?.?-models/' ./corenlp-python/corenlp/corenlp.py.BAK | \
    sed 's/?.?.?.jar/?.?.jar/' > ./corenlp-python/corenlp/corenlp.py

    ## Get CoreNLP:
    cd corenlp-python/
    wget http://nlp.stanford.edu/software/stanford-corenlp-full-2014-06-16.zip
    unzip stanford-corenlp-full-2014-06-16.zip
    rm stanford-corenlp-full-2014-06-16.zip

    # Lexicon
    cd $OSSIAN/tools/downloads
    wget http://www.cstr.ed.ac.uk/downloads/festival/2.1/festlex_CMU.tar.gz
    tar xvf festlex_CMU.tar.gz
    cp festival/lib/dicts/cmu/cmudict-0.4.out ../../corpus/en/labelled_corpora/cmudict/

    # Sequitur G2P
    cd $OSSIAN/tools/
    wget http://www-i6.informatik.rwth-aachen.de/web/Software/g2p-r1668.tar.gz
    tar xvf  g2p-r1668.tar.gz
    rm -r g2p-r1668.tar.gz
    cd g2p

    ## Couldn't compile with clang on mac -- specify to use g++.
    ## Add this in setup.py under 'import os':

## Don't indent this to avoid screwing up the sed expression:
mv setup.py setup.py.BAK
sed 's/import os/import os\
\
os.environ["CC"] = "g++"\
os.environ["CXX"] = "g++"/' setup.py.BAK > setup.py

    ## Compile:
    python setup.py install --prefix  $OSSIAN/tools

    ## training and synth:

    cd $OSSIAN
    rm -r  ./train/en/speakers/tundra_toy_demo/* voices/en/tundra_toy_demo/english_gold_basic
    python ./scripts/train.py -s tundra_toy_demo -l en -p 1 english_gold_basic
    python ./scripts/speak.py -s tundra_toy_demo -l en -o ./test/wav/english_topline.wav english_gold_basic ./test/txt/english.txt

fi



echo
echo ' ------ ran tests, results -------'
echo

if [ $SETUP == 1 ] ; then
    NBIN=`ls $OSSIAN/tools/bin/* | wc -l`
    echo "You have $NBIN binaries in $OSSIAN/tools/bin -- you should have 160 or 163 of them"
    NGLOTT=`ls $OSSIAN/tools/GlottHMM/{Analysis,Synthesis} | wc -l`
    echo "You have $NGLOTT binaries in $OSSIAN/tools/GlottHMM -- you should have 2 (Analysis & Synthesis)"
    
fi

if [ $NAIVE == 1 ] ; then
    for SYNTH in hindi_naive_latinised_glott.wav romanian_toy_naive.wav \
            romanian_toy_naive_glott.wav romanian_toy_naive_glott_prom.wav ; do 
        if [ -e $OSSIAN/test/wav/$SYNTH ] ; then 
            echo "$SYNTH OK"            
        else
            echo "WARNING: $SYNTH should have been synthesised but was not"
        fi
    done
fi


if [ $TOPLINE == 1 ] ; then
    for SYNTH in english_topline.wav ; do 
        if [ -e $OSSIAN/test/wav/$SYNTH ] ; then 
            echo "$SYNTH OK"
        else
            echo "WARNING: $SYNTH should have been synthesised but was not"
        fi
    done
fi