#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
  
import sys
import re
import os

from argparse import ArgumentParser

from util import *

def main_work():

    #################################################

    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-mlf', required=True, help= "...")
    a.add_argument('-trainlist', required=True, help= "...")
        
    opts = a.parse_args()
    # ===============================================
    
    mlf = readlist(opts.mlf)
    trainlist = readlist(opts.trainlist)
    
    mlf_files = [line for line in mlf if re.match('\A"\*.+\.lab\"\Z', line)]
    mlf_files = [line.strip('"*/') for line in mlf_files]
    mlf_files = [line.replace('.lab', '') for line in mlf_files]
    
    trainlist_files = [line.split('/')[-1].replace('.cmp','') for line in trainlist]
    train_dict = dict(zip(trainlist_files, trainlist))
    
    outlist = []
    for f in mlf_files:
        if f in train_dict:
            outlist.append(train_dict[f])
        else:
            print '%s skipped -- no label for it'%(f)
    
    ## overwrite training list:
    writelist(outlist, opts.trainlist)
    
    
if __name__=="__main__":

    main_work()

