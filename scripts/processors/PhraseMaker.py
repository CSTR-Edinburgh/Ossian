#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi


from UtteranceProcessor import SUtteranceProcessor
from util.NodeProcessors import add_phrase_tags, restructure

class PhraseMaker(SUtteranceProcessor):
    '''
    ## Regroup token nodes under new phrase parent nodes:

    ## Group so that phrases are delimited by silence; to find silence, look for 
    ## nodes with attribute segment_name having value sil under each token:
        
    '''

    def __init__(self, processor_name='phrase_maker', node_type_to_regroup='token', parent_node_type='phrase', \
                 attribute_with_silence='segment_name', silence_symbol='sil'):  
        
        self.processor_name = processor_name
        self.node_type_to_regroup = node_type_to_regroup
        self.parent_node_type = parent_node_type
        self.attribute_with_silence = attribute_with_silence
        self.silence_symbol = silence_symbol

        ## derived attribute:
        self.target_xpath='//' + self.node_type_to_regroup
        
        super(PhraseMaker, self).__init__()

    def process_utterance(self, utt):
        
        ### Perform 2 'atomic' operations on the utterance:  

        ## add phrase start / end attributes  on tokens (True/False values):
        add_phrase_tags(utt, target_xpath=self.target_xpath, silence_symbol=self.silence_symbol, \
                                        attribute_with_silence=self.attribute_with_silence)
  
        ## Use those attributes to restructure the utterance using a generic
        ## restructuring function:
        restructure(utt, regroup_nodes_of_type=self.node_type_to_regroup, 
                    start_criterion="phrase_start", end_criterion="phrase_end", 
                    new_parent_type="phrase")
        

