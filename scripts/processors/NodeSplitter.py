#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

from UtteranceProcessor import *

class NodeSplitter(UtteranceProcessor):
    """
    Split contents of node's parent_attribute on delimiter, make children
    of node with tag child_tag and add split contents of parent_attribute
    as child_attribute, one chunk per child.

    Using the defaults, this provides very crude tokenisation on whitespace. 
    """



    def load(self):  

        ## get attributes from config, converting type and supplying defaults:
        self.target_nodes = self.config.get('target_nodes', '//')
        self.split_attribute = self.config.get('split_attribute', 'some_attribute')
        self.child_node_type = self.config.get('child_node_type', 'some_child_type')
        
        
#         #print  dir(self.shared_models[self.my_model])
#         #func_name = self.config['function_to_apply']
#         
#         #self.my_function = getattr(self.shared_models[self.my_model], self.config['function_to_apply'])
#         #print self.my_function
#         #sys.exit(1)
        
    def process_utterance(self, utt):
#         print "-----"
#         print "-----"
#         utt.pretty_print()
#         print "-----"
#         print self.target_nodes
#         print utt.xpath(self.target_nodes)
        for node in utt.xpath(self.target_nodes):
            assert node.has_attribute(self.split_attribute)
            to_split = node.get(self.split_attribute)
            
            child_chunks = self.splitting_function(to_split)
            
            for chunk in child_chunks:
    
                child = Element(self.child_node_type)
                child.set(self.split_attribute, chunk)
                node.add_child(child)

#         utt.pretty_print()

    def splitting_function(self, instring):
        ## Default -- burst into list. Replace this in subclasses.
        return list(instring)


    def do_training(self, speech_corpus, text_corpus):
       return
       
       
       
       
       
       