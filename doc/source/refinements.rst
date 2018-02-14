Tutorial: refining the minimal voice
======================================

.. warning:: all of this section is messy and needs checking

The above example illustrated the basic operation of the tools. But it’s a trivial example. Leaving aside a moment the lack of speech output at run time, the structures actually built have lots of shortcomings.


--text representations -- “ “ (whitespace) is not a happy string for lots of tools to work with, neither are the non-ascii XYZ, neither would things like + be good with e.g. HTK.

--no difference is yet made between punctuation, space and word tokens
--case
--no end sil

These problems are addressed in the following demos:


``demo02``: safetext
---------------------

demo02 builds on demo01 but refines it by adding 2 processors to both the train and runtime pipelines:  token_safetexter, letter_safetexter. These are both of class SafeTextMaker, which in turn builds on NodeEnricher.  Summary: 

    ‘“Refines UtteranceProcessor to enrich the target nodes of the utterance to
    which it is applied by taking the target node's input_attribute, performing
    some enriching_function on it, and writing the result to the target node's 
    output_attribute.
    
    The enriching_function should be provided to subclasses.”

SafeTextMaker takes input_attribute (for these processors, configured to be ‘text’) and adds output_attribute (here, ‘safetext’) which is its safetext.   This is a version of a string which is safe to use with applications of interest (e.g. in HTK modelnames), and has a 1-1 mapping with the plain string. A perhaps over-cautious subset of ASCII is used for this (uppercase A-Z). To enable reverse mapping (NO LONGER PLAN TO USE THIS: note that letter splitter splits original text rather than safetext), multicharacter safetexts are delimited with _.  Safetexts are made for arbitrary unicode characters by looking up their name in the unicode database and sanitising the output (removing spaces, numerals etc.) [NEED TO CHECK UNIQUENESS PRESERVED AFTER THIS CLEANING UP...]

Executing:

.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm demo02 



should give the utterance structure (at ``$OSSIAN/train/rm/speakers/rss_toy_demo/naive/utt/*.utt``):

.. code-block:: xml

    <utt text="Atenţie eu sunt şeful aici." status="OK" waveform="/Users/owatts/repos/simple4all/Ossian/branches/cleaner_june_2013/corpus/romanian/speakers/toy/wav/adr_diph1_009.wav" utterance_name="adr_diph1_009" processors_used=",tokeniser,token_safetexter,letter_adder,letter_safetexter">
      <token text="Atenţie" safetext="aten_LATINSMALLLETTERTWITHCEDILLA_ie">
        <letter text="A" segment_name="a"/>
        <letter text="t" segment_name="t"/>
        <letter text="e" segment_name="e"/>
        <letter text="n" segment_name="n"/>
        <letter text="ţ" segment_name="_LATINSMALLLETTERTWITHCEDILLA_"/>
        <letter text="i" segment_name="i"/>
        <letter text="e" segment_name="e"/>
      </token>
      <token text=" " safetext="_SPACE_">
        <letter text=" " segment_name="_SPACE_"/>
      </token>
      <token text="eu" safetext="eu">
        <letter text="e" segment_name="e"/>
        <letter text="u" segment_name="u"/>
      </token>

    [...]

Note that the goal of safetext is not primarily readability of scripts unfamiliar to the system builder:  _LATINSMALLLETTERTWITHCEDILLA_ is a very verbose way of representing ţ, but at least one that is HTK compatible.

Safetexting simultaneously lowercases -- this function should probably be separated.

``demo03``: end-of-sentence tokens
-----------------------------------


.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm demo03
    
``demo03`` builds on ``demo02`` by modifying the tokeniser’s configuration so that it adds end-of-sentence tokens. These are necessary if, as is likely, we have silences at the beginnings and ends of our training utterance. In that case, such a symbol is needed so that acoustic models representing silence can be attached to something. 

Adding the symbol ‘_END_’ with no further modifications has obviously had a bad effect:

.. code-block:: xml

    <utt text="Atenţie eu sunt şeful aici." status="OK" waveform="/Users/owatts/repos/simple4all/Ossian/branches/cleaner_june_2013/corpus/romanian/speakers/toy/wav/adr_diph1_009.wav" utterance_name="adr_diph1_009" processors_used=",tokeniser,token_safetexter,letter_adder,letter_safetexter">
      <token text="_END_" safetext="_END_">
        <letter text="_" segment_name="_LOWLINE_"/>
        <letter text="E" segment_name="e"/>
        <letter text="N" segment_name="n"/>
        <letter text="D" segment_name="d"/>
        <letter text="_" segment_name="_LOWLINE_"/>
      </token>
      <token text="Atenţie" safetext="aten_LATINSMALLLETTERTWITHCEDILLA_ie">
        <letter text="A" segment_name="a"/>
        <letter text="t" segment_name="t"/>
        <letter text="e" segment_name="e"/>
        <letter text="n" segment_name="n"/>
        <letter text="ţ" segment_name="_LATINSMALLLETTERTWITHCEDILLA_"/>
        <letter text="i" segment_name="i"/>
        <letter text="e" segment_name="e"/>
 
This problem (among others) can be solved by classifying tokens and treating them specially according to their class.

``demo04``: token classifier added 
-------------------------------------


.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm demo04
    
demo4 builds on 3 by adding the processor [token_classifier]. 

RegexClassifier: ‘Classifies nodes based on comparing their input_attribute against a sequence
    of classes and associated regular expressions. The sequence is specified in
    a config subsection. The sequence is iterated through, when a pattern is matched
    the search stops and the class corresponding to the matched pattern is assigned to 
    the node under output_attribute. If none are matched, default_class is assigned.'

Note that non-standard Python regular expressions are used in this example. These match against Unicode Character classes for greater language-naivety. To do this, we use non-standard issue Python regular expression module, regex (https://pypi.python.org/pypi/regex), which is  "intended eventually to replace Python's current re module implementation." This has allowed lots of ropey stuff for doing this which was in previous versions of Ossian to be chopped.

Note also in ``demo04`` the use of the [DEFAULT] section, and string interpolation to break down regular expressions, and possibly reuse them between processor configs.

Note the xpath of processor X is altered to restrict its target nodes to XYZ

Note that safetexter doesn’t apply to the TERMINAL_SYMOBL, and that token clasifier handles TERMINAL_SYMOBL automatically.


``demo05``: adding silences (crudely)
-----------------------------------


.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm demo05
    
Modifiying the xpath for target_nodes of [letter_adder] in demo04 means that letters are only added to tokens classified as words. We also need to add letters [SEGMENTS] corresponding to silences. For this we add 2 processors of a class whose very simple operation is to add a child node with a given tag, having an attribute with a given value to the target_nodes of an utterance, SimpleChildAdder.  [silence_adder] adds a ‘letter’ [SEGMENT] child to tokens which have been classified as punctuation; its text is ‘sil’ (to represent silence). [endsilence_adder] does the same for terminal nodes. [PROBLEM: _END_ in config, but TERMINAL constant in code]


``demo06``: detecting silences from audio, predicting them crudely 
----------------------------------------------------------------

.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm demo06
    
.. warning:: this recipe is incomplete

Demo05’s approach to adding silences at punctuation is a reasonable one at synthesis time, but not so good in training where we can detect silences from the audio. Here the training and runtime pipelines diverge for the first time -- we’ll use demo05’s approach at runtime, but add an aligner for training. 



Before applying the aligner, we need to extract appropriate acoustic features (processor: speech_feature_extractor) 

Before applying the aligner, we also need to dump appropriate labels to be aligned from the utterances (processor: align_label_maker).

.. todo:: Come back and make this recipe functional


``baseline01``: getting speech out
----------------------------------------------


.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm baseline01 
    
We are now in a position to train the system and get speech out of it. To demo06, we need to add a label maker (which makes full context labels from utterance structures) and an acoustic model.

.. todo:: Add details

.. warning:: need to check this runs OK

``baseline02``:  add silence predictor
--------------------------------------------------


.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm baseline02
    
.. todo:: Add information

.. warning:: need to check this runs OK

``baseline03``: add phrase structure
----------------------------------------


.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm baseline03
    
Added phraser and contexts in labeller. Explain phraser’s params.

.. todo:: Add information

.. warning:: need to check this runs OK

``baseline04``: add word VSM
------------------------------------


.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm baseline04
    
Added word_vsm and new contexts for break predictor

.. todo:: Add information

.. warning:: need to check this runs OK

``baseline05``: add letter VSM
------------------------------------


.. code-block:: bash

    ## Train:
    python ./scripts/train.py -s rss_toy_demo -l rm baseline05 
    
.. todo:: Add information

.. warning:: need to check this runs OK

``naive``
------------------------------------


``baseline05`` essentially gives the naive recipe used for the voices described in
`this paper <http://www.cstr.ed.ac.uk/downloads/publications/2013/ssw8_OS2-3_Watts.pdf>`_
already mentioned, called ``naive``. The final ``naive`` recipe  incorporates a couple of minor extra changes:

- the regular expression used for tokenisation is modified so that word-internal punctuation
  (e.g. hyphens) does not end up as a separate token (we found this change useful for Romanian
  and Portuguese, and not harmful for the other languages).
- in ``label_maker``, question_filter_threshold is added and set to 5: this means that 
  questions covering less than 5% or more than 95% of models (counted by token, not type) 
  are removed before building acoustic models. This speeds up decision tree building.
- In training_settings of acoustic_model, BINMOD is set to output HTK binary format models
  during model training -- this is bad in terms of following what's going on, but good for
  speeding up voice building.
