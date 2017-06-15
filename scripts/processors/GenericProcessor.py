#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi


import tempfile 
from UtteranceProcessor import *
import util.NodeProcessors
import logging

class GenericProcessor(UtteranceProcessor):

    '''
    '''

    def load(self):

        assert self.config["function_name"] in dir(util.NodeProcessors)
        self.function = getattr(util.NodeProcessors, self.config["function_name"]) 

        ### Could give the poss of calling fuction with args, but keep it simple for now:
        ##        self.function_args = {}
        ##        if "function_args" in self.config:
        ##            for (k,v) in self.config["function_args"].items():
        ##                self.function_args[k] = v


    def process_utterance(self, utt):

#         if utt.has_attribute(self.config["skip_condition"]):
#             pass
#         else:
        for node in utt.xpath(self.config["target_nodes"]):
            self.function(node)  ##  , **self.function_args)  ## see above


    def do_training(self, speech_corpus, text_corpus):
        print 'GenericProcessor requires no training'
        return


