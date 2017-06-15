#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


import os
import re

   
def nullhed(dirname):
    '''Make empty null.hed file, return its name'''
    fname = os.path.join(dirname, 'null.hed')
    open(fname, 'w').close()
    return fname

def writelist(data, fname):
    f = open(fname, "w")
    f.write("\n".join(data) + '\n')
    f.close()
    
def readlist(fname):
    f = open(fname)
    lines = f.readlines()
    f.close()
    return [line.strip(' \n') for line in lines]
    
def htk_to_sec(htk_time):
    """
    Convert time in HTK (100 ns) units to sec
    """
    if type(htk_time)==type("string"):
        htk_time = float(htk_time)
    return htk_time / 10000000.0

def htk_wildcard_pattern_to_regex(pattern):
    pattern = pattern.strip('{}').split(',')
    chunks = []
    for chunk in pattern:
        chunk = re.escape(chunk)
        chunk = chunk.replace('\*', '.*')
        chunk = chunk.replace('\?', '.')
        chunks.append(chunk)
    new_chunks = '(' + '|'.join(chunks)  + ')'
    reg = re.compile(new_chunks)
    return reg