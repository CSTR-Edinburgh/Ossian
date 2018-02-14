
.. note:: A couple of notes on making an intallation of Python that satisfies TASSAL's requirements. Made for Chee Yong, could be more generally useful documentation with some editing.

=======================================
MAKING YOUR OWN PYTHON INSTALLATION 
=======================================


On Linux
--------

Make a directory for your Python installation:

MYPYTHON=~/temp/python  ## your chosen directory might be e.g. /afs/inf.ed.ac.uk/group/cstr/projects/simple4all/malay/chee_yong_tools/python

mkdir $MYPYTHON

With a browser go to:

http://www.activestate.com/activepython/downloads

... click on the link for Python version 2.7.2.5 for Linux (x86_64) to download the package.
When you've done this, move the package to the current directory (or wherever you want to install it):

mv ~/Downloads/ActivePython-2.7.2.5-linux-x86_64.tar.gz $MYPYTHON

Unpack it:

cd $MYPYTHON
tar xvf ActivePython-2.7.2.5-linux-x86_64.tar.gz 

Use the installer provided to install:

cd ActivePython-2.7.2.5-linux-x86_64
./install.sh

When prompted to specify "Install directory: ", enter ".." to install to $MYPYTHON and type "y" when it asks for confirmation.

This should have installed Python at $MYPYTHON/bin/python -- type it in the command 
line and check you get a Python prompt like this:


[channings]owatts: $MYPYTHON/bin/python
ActivePython 2.7.2.5 (ActiveState Software Inc.) based on
Python 2.7.2 (default, Jun 24 2011, 11:24:26) 
[GCC 4.0.2 20051125 (Red Hat 4.0.2-8)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> 

If that works, type quit() to exit the interactive session.


Use these 3 commands to install numpy, configobj, and lxml (which are all required by TASSAL):

$MYPYTHON/bin/pip install numpy
$MYPYTHON/bin/pip install scipy
$MYPYTHON/bin/pip install configobj
$MYPYTHON/bin/pip install lxml


installation of these on mac with macports
-------------------------------------------

sudo port install py27-lxml
sudo port install py27-configobj 

OR:

sudo port install py27-pip 

###

pip-2.7 install scikit-learn 

## off-topic:

sudo port install R
