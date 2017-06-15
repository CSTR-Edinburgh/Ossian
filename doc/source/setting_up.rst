Setting up
=================

If you've not already done so, get the latest release of Ossian (1.3) from `here <https://www.inf.ed.ac.uk/research/isdd/>`_ and unpack it:

.. code-block:: bash

    tar xvzf ossian-v.1.3.tgz 
    cd ossian-v.1.3/
    
    ## we'll also make an environment variable $OSSIAN to point here for use in these notes:
    export OSSIAN=$PWD
    

Python & Dependencies
----------------------

You'll need version 2.7 of the Python interpreter with numpy and scipy installed, as well 
as the following packages:




- `lxml <http://lxml.de>`_ (BSD, built on C libraries with MIT) is used for handling 
  utterance structures; it is used instead of core Python XML modules because of 
  features such as full XPATH support.
- `scikit learn <http://scikit-learn.org>`_ (BSD) is used for its implementation of 
  various machine learning algorithms (in preference to R implementations in earlier
  versions of the tools). 
- `regex <https://pypi.python.org/pypi/regex>`_ (Python Software Foundation License) is 
  used in preference to the standard ``re`` for its support of Unicode codepoint 
  properties. It is "intended eventually to replace Python's current re module implementation."
- `configobj <https://pypi.python.org/pypi/configobj/>`_ (BSD) is 
  used in preference to ConfigParser for its support of nested sections and conversion of
  comma-separated config values to Python lists. (In an earlier version of the tools, its 
  ability to perform validation and type conversion was also used, but this is no longer 
  the case.)


+++++++++++++++++++++++++++++++++++++++++++++++
Making your own Python installation under Linux
+++++++++++++++++++++++++++++++++++++++++++++++

Here are some steps to install a Python interpreter from scratch for running Ossian,
using the 'Community Edition' distribution at ``http://www.activestate.com/activepython``.
This is just one possible way to install Python.

Make a directory for your Python installation and `cd` to it, and set an environment variable
to point to it for these instructions:

.. code-block:: bash

    export MYPYTHON=$PWD

With a browser go to:

``http://www.activestate.com/activepython/downloads``

and click on the link for Python version 2.7.5.6 for Linux (x86_64) to download the package.
This 'Community Edition' is for non-commercial or non-production use -- please refer to 
the Activestate license for details.
When you've done this, move the package to the new Python directory:

.. code-block:: bash

    mv ~/Downloads/ActivePython-2.7.5.6-linux-x86_64.tar.gz $MYPYTHON

Unpack it:

.. code-block:: bash

    cd $MYPYTHON
    tar xvf ActivePython-2.7.5.6-linux-x86_64.tar.gz 

Use the installer provided to install:

.. code-block:: bash

    cd ActivePython-2.7.5.6-linux-x86_64
    ./install.sh

When prompted to specify "Install directory: ", enter ".." to install to $MYPYTHON and type "y" when it asks for confirmation.

This should have installed Python at $MYPYTHON/bin/python -- type it in the command 
line and check you get a Python prompt like this:

.. code-block:: bash

    ActivePython 2.7.5.6 (ActiveState Software Inc.) based on
    Python 2.7.5 (default, Sep 16 2013, 23:05:39) 
    [GCC 4.0.2 20051125 (Red Hat 4.0.2-8)] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> 

If that works, type ``quit()`` to exit the interactive session.

Add the new Python ``bin`` directory to the start of system path so that the new Python 
will be used for the rest of the session (you can make this last beyond the session by 
editing e.g. your ``~/.bashrc``):

.. code-block:: bash

    export PATH=$MYPYTHON/python/bin/:$PATH

Use the ``pip`` package installer to get some necessary packages:

.. code-block:: bash

    pip install numpy==1.9.1
    pip install scipy==0.14.0
    pip install configobj==4.7.2
    pip install scikit-learn==0.15.2
    pip install regex
    pip install lxml

The version of scikit-learn is probably important; we have not yet determined how much
flexibility there is with the versions of the other packages, but the above combination works.



  

  
 
  
  
  






HTK/HTS, SPTK and hts_engine
----------------------------

Ossian relies on the `HMM-based Speech Synthesis System (HTS) <http://hts.sp.nitech.ac.jp/>`_
for acoustic modelling -- here are some notes on obtaining and compiling the necessary tools. 

The following description again assumes that you have created a directory called ``./ossian-v?.?``
by unpacking an Ossian release, and that an environment
variable ``$OSSIAN`` is set to point to this directory. Also, to get a copy of the HTK source code it
is necessary to register at ``http://htk.eng.cam.ac.uk/register.shtml`` to obtain a 
username and password. It is here assumed that these have been obtained and the environment
variables ``$HTK_USERNAME`` and ``$HTK_PASSWORD`` point to them.

.. note:: Assumes ``wget`` is installed.


.. code-block:: bash

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

To run the Ossian scripts successfully, you will need to apply a second patch before 
compilation. This patch incorporates the following modifications:

    - It extends the functionality of the ``-e`` options of ``HERest`` and ``HSMMAlign``, which we use to speed up training in the Ossian scripts
    - It reverts the ``CM`` function of ``HHEd`` to its HTS 2.2 version -- this is a temporary fix to maintain compatibility with ``hts_engine`` format of version 1.05
    - The model names used by the Ossian scripts are designed to be easier to read and manipulate than those used in e.g. the HTS demo. The disadvantage is that this makes them much longer -- to avoid trouble with long names, we increase the default maximum string length from 1024 to 2048
    - On some data sets we have encountered problems during alignment with invalid transition matrices. A practical solution is to turn the relevant error  (``7031,"PutTransMat: Row %d of transition mat sum``) into a warning, which the patch does.
    
    
    
.. code-block:: bash

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
    
.. note:: 3 tools `da da.sh dawrite` don't build on mac -- why not?


GlottHMM vocoder
----------------

Packaged with Ossian is version 1.0.15 of the `GlottHMM vocoder <http://www.helsinki.fi/speechsciences/synthesis/glott.html>`_.
Compile like this:

.. code-block:: bash

    cd $OSSIAN/tools/GlottHMM/
    make
    
If successful, 2 binaries (``Analysis`` and ``Synthesis``) will have been created in this directory.

.. comment       Messages along the lines of ``ld: library not found for -lconfig`` mean you need to install ``libconfig`` 

Failure might mean you are missing some dependencies, to install these on e.g. on a Mac with Macports, do:

.. code-block:: bash
 
    sudo port install gsl libsndfile libconfig-hr

and then try ``make`` again.

    
Others
----------------------------

.. note:: What other dependencies are there which need mentioning?:-  sox, play ...
