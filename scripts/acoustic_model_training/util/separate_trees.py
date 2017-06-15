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
    a.add_argument('-treefile', required=True, help= "...")
        
    opts = a.parse_args()
    # ===============================================
    
    f = open(opts.treefile, 'r')
    data = f.read()
    f.close()
    trees = re.split('\n\s*\n', data)
    trees = [t for t in trees if t != '']
    
    ## first block is questions:
    questions = trees[0] + '\n\n'
    assert questions[:2] == 'QS'

    tree_dict = {}
    for tree in trees[1:]:
        stream = re.search('(?<=stream\[)[^\]]+(?=\])', tree).group()
        if ',' in stream:
            stream = stream.split(',')[0]
        if stream not in tree_dict:
            tree_dict[stream] = []
        tree_dict[stream].append(tree + '\n\n')

    for (stream, trees) in tree_dict.items():
        writelist([questions] + trees, opts.treefile+'_'+stream)

if __name__=="__main__":

    main_work()

