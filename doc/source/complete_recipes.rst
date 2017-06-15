New improved recipes
======================================

There are several recipes which build on and improve the ``naive`` one already described. Some examples are given here.


``naive_glott``: naive recipe with GlottHMM vocoder
---------------------------------------------------

.. code-block:: bash

    ## Assuming that you want to start from scratch:
    rm -r ./train/rm/speakers/rss_toy_demo/naive_glott/ ./voices/rm/rss_toy_demo/naive_glott/
    
    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm -text wikipedia_10K_words naive_glott
    
    ## Synthesise:
    ./scripts/speak.py -l rm -s rss_toy_demo -o ./test/wav/romanian_toy_naive_glott.wav \
                                            -play naive_glott ./test/txt/romanian.txt
     
     
    
This is the same as the ``naive`` recipe but uses the high-quality vocoder `GlottHMM <http://www.helsinki.fi/speechsciences/synthesis/glott.html>`_ for 
speech analysis and synthesis.

``naive_glott_prom``: wavelet-based prominence labelling 
--------------------------------------------------------

.. code-block:: bash

    ## Assuming that you want to start from scratch:
    rm -r ./train/rm/speakers/rss_toy_demo/naive_glott_prom/ ./voices/rm/rss_toy_demo/naive_glott_prom/
    
    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm -text wikipedia_10K_words naive_glott_prom

    ## Synthesise:
    ./scripts/speak.py -l rm -s rss_toy_demo -o ./test/wav/romanian_toy_naive_glott_prom.wav \
                                            -play naive_glott_prom ./test/txt/romanian.txt
     


This is the same as the ``naive_glott`` recipe but also makes use of an unsupervised
representation of prominence similar to the one described `here <https://tuhat.halvi.helsinki.fi/portal/files/29895386/vainio_etal_trasp2013.pdf>`_. Extraction of the representation is based on wavelet transform-derived  acoustic features and prediction makes use of vector space models of words and a decision 
tree classifier.

Voices from non-alphabetic script data 
--------------------------------------------------------

A Hindi toy corpus (extracted from the IIIT Indic database available `here <http://speech.iiit.ac.in/index.php/research-svl/69.html>`_) is included to demonstrate parts of the recipe developed for the Simple4All
Blizzard Challenge entry described in `this paper <http://www.cstr.ed.ac.uk/downloads/publications/2014/blizzard_14.pdf>`_. 
The recipes ``blizzard_2014_naive_latinised`` and ``blizzard_2014_naive_latinised_syl`` incrementally introduce the naive alphabetisation and syllabification described in the paper. Due to the toy corpus's small size, the syllabification severely affects the quality of the speech.  The recipe ``blizzard_2014_naive_latinised_glott`` adds
the latinisation and GlottHMM vocoder:

.. code-block:: bash

    ## Assuming that you want to start from scratch:
    rm -r ./train/hi/speakers/toy/blizzard_2014_naive_latinised_glott/ ./voices/hi/toy/blizzard_2014_naive_latinised_glott/
    
    ## Train:
    python ./scripts/train.py -s toy -l hi -text wikipedia_10K_words blizzard_2014_naive_latinised_glott
    
    ## Synthesise:
    ./scripts/speak.py -l hi -s toy -o ./test/wav/hindi_naive_latinised_glott.wav \
                 -play blizzard_2014_naive_latinised_glott ./test/txt/hindi.txt 

A simpler recipe like the  ``naive`` one can be used here for comparison:

.. code-block:: bash

    ## Assuming that you want to start from scratch:
    rm -r ./train/hi/speakers/toy/naive/ ./voices/hi/toy/naive/
    
    python ./scripts/train.py -s toy -l hi -text wikipedia_10K_words naive
    
     ./scripts/speak.py -l hi -s toy -o ./test/wav/hindi_naive.wav \
                    -play naive ./test/txt/hindi.txt 
