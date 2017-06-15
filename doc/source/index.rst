.. ossian documentation master file, created by
   sphinx-quickstart on Mon Nov 11 14:45:09 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ossian documentation 
==================================



.. image:: s4a.png
   :height: 100px
   :width: 200 px
   :scale: 50 %
   :alt: alternate text
   :align: right
   
Ossian is a collection of Python code for building text-to-speech (TTS) systems, with an 
emphasis on easing research into building TTS systems with minimal expert 
supervision. Work on it started with funding from the `EU FP7 Project Simple4All <http://simple4all.org>`_.



A core idea of Ossian is that a lot of the work for making a Python TTS system 
can be done by using existing modules. For example, instead of writing a module for 
manipulating and querying utterance structures from scratch, we can use existing XML 
and  XPATH implementations. Instead implementing a decision tree learning from 
scratch, we can use simply 
design the tools to work with existing open source machine learning packages, with the 
obvious benefit that many different methods besides decision trees are implemented with 
a unified interface. By depending on relevant Python core or 3rd party packages, we aim
to make the original code of Ossian as minimal as possible.   


If you are interested only in running existing voices, please take a look at *Setting up* and *Basic operations*.
If you plan to build voices using already-defined recipes, these will also be helpful.
If you plan to extend existing recipes or write new ones, the *Tutorial* sections might be of use.


The online version of this documentation `here <http://homepages.inf.ed.ac.uk/owatts/ossian/html/index.html>`_ is often more up-to-date than the one included with releases of the code.

Contents:

.. toctree::
   :maxdepth: 4
   
   setting_up
   
   basic
   complete_recipes
   
   gold_standard_recipes
   acoustic_modelling_scripts
   
   initial_voice
   refinements

   todo_list
  


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

