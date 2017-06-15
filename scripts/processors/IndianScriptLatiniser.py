#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

from naive.naive_util import *
import unicodedata
import glob
from processors.UtteranceProcessor import *
from processors.NodeSplitter import *
from processors.NodeEnricher import *
import datetime

from naive import naive_util

from util.indian2latin import latinise_indian_script_string

import default.const as c

class IndianScriptLatiniser(NodeSplitter):
    '''
    Alphabetise indian language alphasyllabic representations of words, and add
    the alphabetic representations as children
    '''
    def load(self):
        NodeSplitter.load(self)
        
        ## TODO: tidier way to use as_bool with default values
        try:
            self.add_terminal_tokens = self.config.as_bool('add_terminal_tokens')
        except KeyError:
            self.add_terminal_tokens = False
        
    def splitting_function(self, instring):
        tokens = latinise_indian_script_string(instring)
        tokens = [t for t in tokens if t != '']
        if self.add_terminal_tokens:
            tokens = [c.TERMINAL] + tokens + [c.TERMINAL]
        return tokens 
        
    def do_training(self, speech_corpus, text_corpus):
        print "IndianScriptLatiniser requires no training"    



