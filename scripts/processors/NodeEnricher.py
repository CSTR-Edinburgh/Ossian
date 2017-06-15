#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

from UtteranceProcessor import *

class NodeEnricher(UtteranceProcessor):
    """
    Refines UtteranceProcessor to enrich the target nodes of the utterance to
    which it is applied by taking the target node's input_attribute, performing
    some enriching_function on it, and writing the result to the target node's 
    output_attribute.
    
    The enriching_function should be provided to subclasses.
    """

    def load(self):  

        ## get attributes from config, converting type and supplying defaults:
        self.target_nodes = self.config.get('target_nodes', '//')
        self.input_attribute = self.config.get('input_attribute', 'text')
        self.output_attribute = self.config.get('output_attribute', 'some_attribute')
        
        
    def process_utterance(self, utt):
#         print "-----"
#         print "-----"
#         utt.pretty_print()
#         print "-----"
#         print  self.target_nodes
        for node in utt.xpath(self.target_nodes):
            assert node.has_attribute(self.input_attribute)
            input = node.get(self.input_attribute)
            
            transformed = self.enriching_function(input)
            
            node.set(self.output_attribute, transformed)

#         utt.pretty_print()
        
    def enriching_function(self, input):
        raise NotImplementedError, 'Please provide an enriching_function when subclassing NodeEnricher'  
        

    def do_training(self, speech_corpus, text_corpus):
        return
       
   
class AttributeAdder(NodeEnricher):
    '''
    Can be used to add attributes to target nodes, also to overwrite existing ones.
    '''
    def load(self):
        NodeEnricher.load(self)
        self.output_value = self.config.get('output_value', 'some_value')
        
    def enriching_function(self, input):
        return self.output_value
   
   
       
