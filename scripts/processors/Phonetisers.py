#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Ossian - May 2017  
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk

from processors.UtteranceProcessor import SUtteranceProcessor, Element
from naive import naive_util
import default.const as c


# import os
# import sys
# import re
# import regex
# import unicodedata
# import shutil
# import glob 
# import fileinput
# import subprocess
# import codecs 

# import default.const as c

# from processors.NodeEnricher import NodeEnricher
# from processors.UtteranceProcessor import UtteranceProcessor

# from util.LookupTable import LookupTable

# from naive.naive_util import readlist, writelist


class NaivePhonetiser(SUtteranceProcessor):
    '''
    Add 'phonetic' segments consisting of standard orthography characters, converted into an ASCII-safe 'safetext' form
    '''
    def __init__(self, processor_name='naive_phonetiser', target_nodes="//token", \
                target_attribute='text', child_node_type='segment', output_attribute='pronunciation', \
                class_attribute='token_class', word_classes=['word'], probable_pause_classes=['punctuation', c.TERMINAL], \
                possible_pause_classes=['space']):

        self.processor_name = processor_name
        self.target_nodes = target_nodes
        self.target_attribute = target_attribute
        self.child_node_type = child_node_type
        self.output_attribute = output_attribute
        self.class_attribute = class_attribute
        self.word_classes = word_classes
        self.probable_pause_classes = probable_pause_classes
        self.possible_pause_classes = possible_pause_classes

        super(NaivePhonetiser, self).__init__()

    def process_utterance(self, utt):
        for node in utt.xpath(self.target_nodes):
            assert node.has_attribute(self.class_attribute)
            assert node.has_attribute(self.target_attribute)

            current_class = node.attrib[self.class_attribute]

            if current_class in self.word_classes:
                word = node.attrib[self.target_attribute]
                children = self.get_phonetic_segments(word)
            elif current_class in self.probable_pause_classes:
                children = [c.PROB_PAUSE]
            elif current_class in self.possible_pause_classes:
                children = [c.POSS_PAUSE]
            else:
                sys.exit('Class "%s" not in any of word_classes, probable_pause_classes, possible_pause_classes')
            for chunk in children:
                child = Element(self.child_node_type)
                child.set(self.output_attribute, chunk)
                node.add_child(child)

    def get_phonetic_segments(self, word):
        safetext_letters = []
        for letter in list(word.lower()):
            safetext_letters.append(naive_util.safetext(letter))
        return safetext_letters

    def do_training(self, speech_corpus, text_corpus):
        print "NaivePhonetiser requires no training"    


