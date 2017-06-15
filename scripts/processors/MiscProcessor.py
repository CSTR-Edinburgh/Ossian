#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

'''
These are mainly one-use things which I found useful in specific cases. Often hardcoded
and not configurable...
'''
import codecs

from UtteranceProcessor import *
from NodeEnricher import NodeEnricher, AttributeAdder

class TextPrinter(UtteranceProcessor):

    '''
    '''

    def load(self):

        self.target_nodes = '//token'


    def process_utterance(self, utt):

        accum_text = ""

        for token in utt.xpath(self.target_nodes):
            if token.get('token_class') != '_END_':
                if token.get('token_class') == 'space':
                    if  token.get('has_silence') == 'yes':
                        accum_text += ', '  ## add a comma
                    else:
                        accum_text += ' '            
                elif token.get('token_class') == 'punctuation':
                    if  token.get('has_silence') == 'yes':
                        accum_text += token.get('text')
                    else:
                        accum_text += ' '
                else:    
                    accum_text += token.get('text')

        
        outf = utt.get_filename('txt_punc')
        f = codecs.open(outf, 'w', encoding='utf-8')
        f.write(accum_text)
        f.close()
                 
    def do_training(self, speech_corpus, text_corpus):
        print 'TextPrinter requires no training'
        return


class BadDataMasker(NodeEnricher):
    '''
    The intended use of this class is to allow phones [e.g. a] to be
    rewritten in 'marked form' (e.g. a_MASKED) conditioned on position 
    and attributes in utterance structure. This is so there are 
    models to soak up bad data in alignment but keep the models 
    built on good data pure. The masked versions will never be used in
    synthesis. E.g. if our LTS is bad, we could mask phones in words
    which are OOV. Ditto for number words where our number normalisation
    is known to be poor. 
    '''
    def enriching_function(self, input):
        return input + '_BAD_DATA_MASKED'


