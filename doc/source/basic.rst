================
Basic operations
================

Here are some examples of basic usage of Ossian. Instructions given for building all voices in this documentation use tiny amounts of data (a few minutes) for training. This is to speed up the time it takes to run these demos, but it means the quality of the voices  is very low. However, all databases used are publicly available in full, so building full versions of these voices is possible. Trained voices built on larger data sets will be made available in the near future.
 

Installing existing voices
------------------------------------------------------

To demonstrate how to install a voice that has already been built and packaged up, 
examples of such voices are included with releases of Ossian, in ``$OSSIAN/example_voices``.
``rm-rss_toy-naive_example`` is an example of a voice trained on just a couple of minutes of
the `Romanian Speech Synthesis Database <http://romaniantts.com/new/rssdb/rssdb.php>`_.
To install it, just unpack it:

.. code-block:: bash

    cd $OSSIAN/  ## voice will unpack relative to this location
    tar xvf ./example_voices/rm-rss_toy-naive_example.tar
    
The data for building this simple voice is included under ``./corpus``.

.. comment
..
.. SKIP BIGGER VOICE FOR NOW:-
..
.. ``rm-rss_rnd1-naive_example`` is an example of a better voice trained on 38 minutes from the same corpus and .. 1M words of text is here. You can install it too:
..
.. .. code-block:: bash
..
..    cd $OSSIAN/  ## voice will unpack relative to this location
..    tar xvf example_voices/rm-rss_rnd1-naive_example.tar 



    
Synthesis from installed voices
----------------------------------------------------

To synthesise from the voice we have just installed using  textfile as input:


.. code-block:: bash

    cd $OSSIAN/  
    ./scripts/speak.py -l rm -s rss_rnd1 \
            -play naive ./test/txt/romanian.txt
            

To do the same, but store audio to file:

.. code-block:: bash

    ./scripts/speak.py -l rm -s rss_rnd1 \
            -o ./test/wav/romanian_rnd1_naive.wav naive ./test/txt/romanian.txt
     
     
     
The script ``speak.py`` accepts input from stdin in the absence of filenames on the
command line, so we can use it interactively:

.. code-block:: bash

    cd $OSSIAN/  
    while read textin ; do 
        echo $textin | ./scripts/speak.py -l rm -s rss_rnd1 \
            -play naive ; 
        echo "Type your text here:" ;
    done
    
... and press CTRL+C to end the session.

Try the same for the small 2 minute voice for comparison: 

.. code-block:: bash

    cd $OSSIAN/  
    while read textin ; do 
        echo $textin | ./scripts/speak.py -l rm -s rss_toy_demo \
            -play naive_example ; 
        echo "Type your text here:" ;
    done
    
    
    
    
Training a new voice from an existing recipe
----------------------------------------------------

This shows how to build a Romanian (``rm``) voice on the very small ``rss_toy_demo`` 
speech corpus using the ``naive`` recipe -- it will be the same as the existing voice 
installed above.
This recipe is essentially that used for the voices described in
`this paper <http://www.cstr.ed.ac.uk/downloads/publications/2013/ssw8_OS2-3_Watts.pdf>`_.


.. code-block:: bash

    ## Assuming that we want to start from scratch:
    rm -r ./train/rm/speakers/rss_toy_demo/naive/ ./voices/rm/rss_toy_demo/naive/

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm -text wikipedia_10K_words naive 

The ``-text`` flag is used to specify an extra large text corpus used for training vector space models, in addition to the speech transcripts.

To test the resulting voice (it should be the same as the installed one apart from the name):

.. code-block:: bash

    ./scripts/speak.py -l rm -s rss_toy_demo \
            -o ./test/wav/romanian_toy_naive.wav naive ./test/txt/romanian.txt
     
     




Packing up a trained voice
----------------------------------------------------

To make a packed version of a voice that others can install:

.. code-block:: bash

    cd $OSSIAN/  ## pack up voice relative to this location
    ## Rename the voice as you like by appending something to the name:
    cp -r  ./voices/rm/rss_toy_demo/naive/ ./voices/rm/rss_toy_demo/naive_example_02/
    tar cvf ./example_voices/rm-rss_toy-naive_example_02.tar voices/rm/rss_toy_demo/naive_example_02/ 
    
    
    
Training a voice in a new language
----------------------------------------------------

If you have text and wav files in a particular language, you can try training a voice as follows. 

1. Choose a name or abbreviation for your language and dataset/speaker. These are arbitrary -- just choose   strings that are memorable for you. Then make the following directories, substituting ``<LANG>`` and ``<SPEAKER>`` for your chosen strings:

   .. code-block:: bash

    ossian-v.1.3/corpus/<LANG>/speakers/<SPEAKER>/txt
    ossian-v.1.3/corpus/<LANG>/speakers/<SPEAKER>/wav

   For example, the example demo for the toy Romanian system uses 'rm' and 'rss_toy_demo' as the ``<LANG>`` and ``<SPEAKER>`` names, and so you can find the data here:

   .. code-block:: bash

    ossian-v.1.3/corpus/rm/speakers/rss_toy_demo/txt
    ossian-v.1.3/corpus/rm/speakers/rss_toy_demo/wav

2. Put your txt and wav data in the newly-created ``./txt/`` and ``./wav/`` directories.

3. Choose a recipe and build a voice using it. For a language with an alphabetic writing system, the ``naive`` recipe is a good starting place. For languages with alphasyllabic systems (e.g. Indian languages), the recipe ``blizzard_2014_naive_latinised_glott_syl`` might make a starting point (`this paper <http://www.cstr.ed.ac.uk/downloads/publications/2014/blizzard_14.pdf>`_ tells you a bit about it). Both these recipes are designed to be as language-independent as possible -- if you are able to add language-specific knowledge to make a more specialised you might get better results. 
 
   To run e.g. the 'naive' recipe on your data, do this:

   .. code-block:: bash

      python ./scripts/train.py -s <SPEAKER> -l <LANG> naive

4. If training goes OK, the voice will be output here:

   .. code-block:: bash

     ossian-v.1.3/voices/<LANG>/<SPEAKER>/naive/

   Intermediate files not needed for running the final voice but which might be useful for further training and analysis (including e.g. .lab, .utt and .cmp files) will be output here:

   .. code-block:: bash

       ossian-v.1.3/train/<LANG>/speakers/<SPEAKER>/naive/

5. Optionally, add a large text corpus for your language before training. Choose a name for it (``<TEXT_CORPUS_NAME>``) and make this directory:

   .. code-block:: bash

    ossian-v.1.3/corpus/<LANG>/text_corpora/<TEXT_CORPUS_NAME>

  and put 1 or more .txt files inside that directory. To use this corpus in training, call the script like this:

   .. code-block:: bash

       python ./scripts/train.py -s <SPEAKER> -l <LANG> -text <TEXT_CORPUS_NAME>  naive



