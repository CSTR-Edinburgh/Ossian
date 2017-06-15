#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi


import sys, os
from string import strip
import codecs


"""
This script takes a Festival-style utts.data file with lines like

( utt_name "Some text." )

... and outputs a directory of single-line text files in utf-8 called e.g. 
utt_name.txt with contents like e.g. 

Some text

Input encodings is assumed to be ASCII unless stated as a 3rd argument on the
command line (e.g. iso-8859-1)

"""


def main_work():

    #################################################

    # ======== Get stuff from command line ==========

    def usage():
        print "Usage: ......  "
        sys.exit(1)

    # e.g. 

    source_encoding = "ascii"  ## initialise with default encoding, ASCII

    try:
        uttsdata = sys.argv[1]
        text_dir = sys.argv[2]
        if len(sys.argv) > 3:
            source_encoding = sys.argv[3] ## change encoding here

        
    except:
        usage()


    #################################################
    if not os.path.isdir(text_dir):
        os.mkdir(text_dir)
    
    target_encoding = "utf-8"     
    
    data = codecs.open(uttsdata, "r", source_encoding).readlines()  
    data = [line.strip("\n ()") for line in data]
    text = [" ".join(line.split(" ")[1:]) for line in data]    
    names = [line.split(" ")[0] for line in data]   
    text = [line.strip('" ') for line in text]    

    for (name, words) in zip(names, text):
        print "Write text of utt %s, from %s to utf-8"%(name, source_encoding)
        f=codecs.open(os.path.join(text_dir, name + ".txt"), "w", target_encoding)
        f.write(words)
        f.close()


if __name__=="__main__": 

        main_work()


