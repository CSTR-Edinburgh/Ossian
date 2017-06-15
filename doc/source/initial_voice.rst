

Tutorial: building a minimal voice
===================================


To give some idea of how Ossian works we will demonstrate the building of the 
most simple  'voice' possible.
This 'voice' is very basic and won't in fact speak, but should give a general 
idea of how the tools work. The following discussion assumes that an environment
variable ``$OSSIAN`` is set to point to the top directory of the tools as before.


.. code-block:: bash

    cd $OSSIAN
    python ./scripts/train.py -s rss_toy_demo -l rm demo01

This instructs Ossian to use the 'rss_toy_demo' corpus in Romanian (``rm``) to build a voice using the 
recipe we've called ``demo01``. Ossian expects the corpus to be stored at:

.. code-block:: bash

    $OSSIAN/corpus/rm/speakers/rss_toy_demo/

and intermediate data/models for the voice are kept at: 

.. code-block:: bash

    $OSSIAN/train/rm/speakers/rss_toy_demo/demo01
    
and components of the final trained voice will be output at:

.. code-block:: bash

    $OSSIAN/voices/rm/rss_toy_demo/demo01

The key work of the ``train.py`` script is to:

- create a corpus object from the data specified by the language and corpus name
- create a voice object initialised to use the specified recipe
- train the voice by calling ``voice.train(corpus)`` using the objects which have been 
  constructed in the previous two steps.

These three steps are now described in greater depth.



Corpus loading
--------------

.. todo:: Add some notes on corpus here -- holds collections of utterances and text.

.. comment:: include description of XML utterance struct

.. comment::  Corpus 

.. comment:: represent relations between utterances (if utterances are sentences, then this extra structure might represent paragraphs or chapters).

Utterance
+++++++++

.. todo:: tidy this up a bit

Utterances have hierarchical structure, and for TTS it’s useful to have a representation of that. E.g. word dominates syllables, syllables dominate phone segments, phone has attribute of start time. Storing this data as a tree whose nodes have attributes allows other useful representations to be inferred (e.g. sequence of syllables grouped into words, find start time of word, etc.) 

For Ossian, we decided to use XML representation of utterance structure (where utterance structure is represented by XML document structure). The advantages are we’ve used it before for this purpose, existing XML libraries can be used, existing general standards for querying trees (XPATH). Disadvantages: speed, tree (where each node has only 1 parent) more restrictive than e.g. Festival’s utterance structure (syllables not always aligned with morphs; word in both phrase and syntax relations).

Utt class for loading/storing utt structure from/to XML. Data associated with utterance is stored in tree as attributes (e.g. type of Token). In some cases, this can be a filepath to data stored external to the utterance. This is useful for large and/or non-text data (waveforms, MFCCs etc.), also for files required in specific formats for other tools (e.g. label files).





Text data
+++++++++
Currently treated separately -- consistency would involve putting all text data also in utterance structures. We have experimented with this, but (predictably) speed is an issue with even 
modestly-sized corpora.





Voice initialisation
--------------------

An untrained voice is initialised using a config file (.ini format) corresponding to a *recipe* (in ``$OSSIAN/recipes/*.cfg``).   The recipe config file for a recipe called ‘x’ is expected to be located in ./recipe/x.cfg. Take a look at ./recipe/demo01.cfg to get an idea of the required structure.

The basic structure of a Ossian voice is a sequence of utterance processors. When an utterance in a corpus (either the training corpus during training, or a ‘test corpus’ at run time, which in the simplest case will contain only a single utterance) is processed, it is passed along a sequence utterance processors, each of which adds to or modifies the XML of the utterance, sometimes creating data external to the utterance structure.
 
A recipe can specify different sequences of processors (called stages) for different purposes. The first  2 sections in ./recipe/demo01.cfg (called [train] and [runtime]) each contain a list of processors, which happens to be the same in both cases. These are the most important stages of a voice (and the only ones which are required) -- train specifies the processors to be applied during training, and runtime at synthesis. 



.. coment :: Already-trained voices are loaded from their stored config file at e.g.





Voice training 
--------------

The main lines of the train method, slightly simplified, are these:

.. code-block:: python

    def train(corpus):
         for processor in self.processors:
                if not processor.trained:  
                        processor.train(corpus)
              for utterance in corpus:
                    processor.apply_to_utt(utterance) 
                    utterance.save()
         self.save()


Each processor is trained if it is not yet trained, and then applied to the training corpus as it would be in synthesis. The key idea here is that we want the uttearnces to be processed in a way that is consistent at training and run time.  The synthesis-type processing provides possible new training data for downstream use.

In the last line, the voice's ``save`` method is called. The role of this method is to:
copy the minimal files necessary for synthesis with the built voice to the 
``$OSSIAN/voices/`` directory, including a copy of the voice config file.
This means the config can be tweaked after training 
without altering the recipe for voices built in the future.
Also the recipe config can be modified for building future voices without breaking
already-trained ones.


In the ``demo01`` example, no training is done for either processor -- both are applied in series, resulting in utterance structures for training like:

.. code-block:: xml

    <utt text="Nu este treaba lor ce constituţie avem." status="OK" waveform="/Users/owatts/repos/simple4all/Ossian/branches/cleaner_june_2013/corpus/romanian/speakers/toy/wav/adr_diph1_001.wav" utterance_name="adr_diph1_001" processors_used=",tokeniser,letter_adder">
      <token text="Nu">
        <letter text="N"/>
        <letter text="u"/>
      </token>
      <token text=" ">
        <letter text=" "/>
      </token>
      <token text="este">
        <letter text="e"/>
        <letter text="s"/>
        <letter text="t"/>
        <letter text="e"/>
      </token>

    [...]


Similar processing happens for testing. Language-naive: we will add examples on other languages too.




When loading, a voice looks at the list of processors for whatever stage it has been activated in (e.g. train, runtime), and tries to find a section of the recipe with the same name as each one. In the ``demo01`` example, it will look for (and find) a config section entitled [tokeniser]. Each processor will be a Python object whose class is specified with the ‘class’ key in the config.  [tokeniser] says it is to be an object of class BasicTokenisers.RegexTokeniser. Given this class name, the voice uses dynamic loading and tries to instantiate an object of the required class using the config. 

When writing subclasses of UtteranceProcessor, users are expected to provide the methods load() and process_utterance(). Load is meant to do class-specific things after instantiation, including setting default values of required instance attributes, reading user- or recipe-specified values for them from config, converting type as necessary. The definition of ``process_utterance`` specifies what work is to be performed on an utterance which is being synthesied.  

Optionally, for processors which really require training,  ``do_training()`` can be provided (add more here).

A class hierarchy has been developed. There are some abstract subclasses of UtteranceProcessor such as NodeSplitter which provide some functions useful for TTS. 
NodeSplitter is configured with  an XPATH pattern matching its target_nodes,  a split_attribute, and  child_node_type. When an utterance is processed (using process_utterance), the processor pulls out the nodes of the utterance that match the target_node  xpath, for each of those nodes extracts the value  attribute split_attribute from each, splits that value, and adds child nodes of type child_node_type.  This is useful for such tasks as breaking sentences into words, words into syllables, and many other TTS tasks. A user can easily write code to tokenise text just by making a subclass providing a method called splitting_function. The details of reading xpaths and node attribute names from config is all taken care of, as is the tedious detail of manipulating XML (esp. important for more elaborate transformations such as restructuring, where it is very easy to screw up document/chronological order of nodes.) Existing code for e.g. syllabification can be easily integrated by wrapping it in the splitting_function of such a newly defined subclass.
]

In the current example, both processors are to be loaded into 2 differently configured instantiations of the same class, RegexTokeniser. This class specialises NodeSplitter by specifying a splitting_function that uses a regular expression read from config. (Add more detail here)

Split words to letters with simple pattern (.)

Note that () means that the spaces themselves are included in the resulting chunks (and thus children).



