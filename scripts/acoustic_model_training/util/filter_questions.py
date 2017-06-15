#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
  
import sys
import re
import os
import random

from argparse import ArgumentParser

## find location of util relative to current script:
loc = os.path.abspath(os.path.join( __file__, os.pardir, os.pardir, 'util') )
sys.path.append(loc)


from util import *

def main_work():

    #################################################

    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-infile', required=True, help= "...")
    a.add_argument('-outfile', required=True, help= "...")
    a.add_argument('-models', required=True, help= "...")
    a.add_argument('-percent', required=True, type=int, help= "...")

   
    opts = a.parse_args()

    # ===============================================
    
    questions = readlist(opts.infile)
    models = readlist(opts.models)
    
    nmod = float(len(models))
    
    filtered = []
    
    for line in questions:
        print line
        line = line.strip()
        if line != '':
            
            (QS,name,patt) = re.split('\s+', line)
            regex_patt = htk_wildcard_pattern_to_regex(patt)
            for mod in models:
                count = 0
                if re.match(regex_patt, mod):
                    count += 1
                percent_matched = count / nmod
                if percent_matched < opts.percent or percent_matched > (100.0 - opts.percent):
                    pass
                else:
                    filtered.append(line)
            
    writelist(filtered, opts.outfile)
    
if __name__=="__main__":

    main_work()

