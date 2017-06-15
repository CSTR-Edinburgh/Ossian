=============================================
MAKING YOUR OWN PYTHON INSTALLATION ON LINUX
=============================================

Here are some steps to install a Python interpreter from scratch for running Ossian,
using the 'Community Edition' distribution at ``http://www.activestate.com/activepython``.
This is just one possible way to install Python.

Make a directory for your Python installation and `cd` to it, and set an environment variable
to point to it for these instructions:

export MYPYTHON=$PWD

With a browser go to:

``http://www.activestate.com/activepython/downloads``

and click on the link for Python version 2.7.5.6 for Linux (x86_64) to download the package.
This 'Community Edition' is for non-commercial or non-production use -- please refer to 
the Activestate license for details.
When you've done this, move the package to the new Python directory:

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

    pip install numpy==1.8.0
    pip install scipy==0.12.0
    pip install configobj==4.7.2
    pip install scikit-learn==0.13.1
    pip install regex
    pip install lxml

The version of scikit-learn is probably important; we have not yet determined how much
flexibility there is with the versions of the other packages, but the above combination works.



  
  
 
  
  
  