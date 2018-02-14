English gold standard recipe
============================

--------
Overview
--------

The recipes mentioned so far are experimental, language-independent, and geared towards cases where expert knowledge for the target language is lacking. But Ossian is a general framework, and recipes incorporating expert knowledge and language-specific tools can be created. As an example, a recipe for English using many high-quality components is demonstrated. 


For the naive, Blizzard etc. recipes shown so far, we depend only on code with permissive
(MIT, BSD, etc.) licenses. For this topline recipe, it was decided to
depend on less permissively-licensed code (GPL etc.) where it allows us to build voices using
state-of-the-art components. 

The ``english_gold_basic`` recipe makes use of the following knowledge sources and external components:

    1.  Some Apache/MIT licensed perl scripts to do text normalisation: this is code
        used, modified, and partially created at CSTR for normalising text prior to
        training language models for ASR.
        
    2.  Stanford core NLP (GPL) for doing POS tagging (Java), and Python wrappings for it -- 
        corenlp-python (GPL). This also provides a lot of other NLP besides POS 
        (parsing, named-entity recognition, coreference resolution, sentence segmentation...)
        not used here but which can be used in other recipes.
    
    3.  Lexicon: this recipe depends on the CMU pronouncing lexicon. This is really for 
        American English but is used here as a general English lexicon due to lack of 
        restrictions on its use.

    4.  Sequitur G2P (GPL): letter-to-sound based on joint multigrams
    
All this is glued together in Ossian's utterance processing framework, and 
some extra bits and pieces like postlexical rules for handling deletion of final [r] 
in RP English are included in extra processors.

1 is included in the Ossian release; the others are dependencies which users should install before trying to use the recipe -- see next section.

------------
Installation
------------

As before, these instructions assume that you have created a directory called ``./ossian-v1.3`` by unpacking an Ossian release, and that the environment variable ``$OSSIAN`` points to it, 
   
Stanford core NLP with Python bindings
--------------------------------------

.. code-block:: bash

    ## You might need to install some Python packages which the Python bindings depend on:
    sudo pip install pexpect unidecode jsonrpclib simplejson ## which of these are actually necessary?

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


Lexicon
----------

.. code-block:: bash

    cd $OSSIAN/tools/downloads
    wget http://www.cstr.ed.ac.uk/downloads/festival/2.1/festlex_CMU.tar.gz
    tar xvf festlex_CMU.tar.gz 
    cp festival/lib/dicts/cmu/cmudict-0.4.out ../../corpus/en/labelled_corpora/cmudict/

Other necessary resources such as phoneset should already be under ``$OSSIAN/corpus/en/labelled_corpora/cmudict/``


Sequitur G2P
------------

.. code-block:: bash

    cd $OSSIAN/tools/
    wget http://www-i6.informatik.rwth-aachen.de/web/Software/g2p-r1668.tar.gz
    tar xvf  g2p-r1668.tar.gz
    rm -r g2p-r1668.tar.gz
    cd g2p

    ## Couldn't compile with clang on mac -- specify to use g++.
    ## Add this in setup.py under 'import os':

    mv setup.py setup.py.BAK
    sed 's/import os/import os\
    \
    os.environ["CC"] = "g++"\
    os.environ["CXX"] = "g++"/' setup.py.BAK > setup.py

    ## Compile:
    python setup.py install --prefix  $OSSIAN/tools


-----
Usage
-----

We here demonstrate using the recipe by building a voice on a small subset of the English part of the Tundra corpus (available in full `here <http://tundra.simple4all.org>`_).
The option ``-p`` to invoke multithreading in training can interfere with the Stanford Java code -- specify to use a single core (``-p 1``) when using this recipe:

.. code-block:: bash

    cd $OSSIAN
    rm -r  ./train/en/speakers/tundra_toy_demo/* voices/en/tundra_toy_demo/english_gold_basic
    python ./scripts/train.py -s tundra_toy_demo -l en -p 1 english_gold_basic
    python ./scripts/speak.py -s tundra_toy_demo -l en -play english_gold_basic ./test/txt/english_topline.txt 

As well as increasing the amount of data for training a decent voice with this recipe, you will probably also want to alter the settings for ``lts_ntrain`` and ``lts_gram_length`` (e.g. to 0 and 3 respectively).