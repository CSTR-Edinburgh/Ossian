#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

from UtteranceProcessor import *

class SimpleChildAdder(UtteranceProcessor):
    """
    Simplest kind of manipulation, no model. For each node in target nodes, add a child
    with tag child_tag, and child_attribute as child_attribute_value. The xpath given for target nodes
    can be tailored to match the desired set of nodes.
    
    TODO: doc
    """

    def load(self):  

        ## get attributes from config, converting type and supplying defaults:
        self.target_nodes = self.config.get('target_nodes', '//')
        self.child_tag = self.config.get('child_tag', 'some_tag')
        self.child_attribute = self.config.get('child_attribute', 'some_attribute')
        self.child_attribute_value = self.config.get('child_attribute_value', 'some_value')

        
    def process_utterance(self, utt):

        for node in utt.xpath(self.target_nodes):
            child = Element(self.child_tag)
            child.set(self.child_attribute, self.child_attribute_value)
            node.add_child(child)



    def do_training(self, speech_corpus, text_corpus):
       return
       
       
       