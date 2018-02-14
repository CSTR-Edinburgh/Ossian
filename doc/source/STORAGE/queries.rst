Queries
=======



corpus object
-------------

corpus -- contain utt objects, not filenames to avoid this in  e.g. vsm tagger / dt proc.s
 
        for utt_name in speech_corpus:
            utterance = Utterance(utt_name)
            
            
text and speech in copurs
-------------------------
            
in vsmtagger.py:
          
.. todo:: Add the text from the unspoken parts



others
-------

- separate train and voice

- letter vsm uses cross-word contexts...

- lowercasing should be separated from safetexting


Document whole module like this:

.. automodule:: naive.naive_util
   :members:
   
Document functions like this:


.. autofunction:: naive.naive_util.unicode_character_to_safetext



utt mod
--------
.. automodule:: main.Utterance
   :members:
   :undoc-members:

   
TODO list   
---------

.. todolist::