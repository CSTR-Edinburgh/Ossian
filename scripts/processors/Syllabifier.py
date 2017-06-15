#!/usr/bin/env python
# -*- coding: utf-8 -*-

from configobj import ConfigObj
from UtteranceProcessor import *
#import util.NodeProcessors
import logging
import os
import re
import default.const as c
class Syllabifier(UtteranceProcessor):
    



    def load(self):
        self.parent_node_type =  self.config.get('parent_node_type', '//token')
        self.target_nodes = self.config.get('target_nodes', "//token[@token_class='word']/descendant::segment")
        ## read phonetic classes, either unsupervised or human produced
        self.phoneclass_filename = os.path.join(self.get_location()+"/../phonetic_classifier", self.config['phone_classes'])
        #filename = os.path.join(self.voice_resources.get_path(c.LANG), self.config['phone_classes'])
        if os.path.isfile(self.phoneclass_filename):
            self.phones = ConfigObj(self.phoneclass_filename, encoding='utf8')
            # culcurate legexprs on init
            
            self.regexps = self._compile_syllable_regexps()
            self.trained = True
        else:
            self.trained = False

            



    def do_training(self, speech_corpus, text_corpus):

        self.load()  ## because phoneclass_filename prob. didn't exist when processor was first loaded.

        if self.trained == True:
            return
        if self.phones:
            self.regexps = self._compile_syllable_regexps()
            self.trained = True

            

        
        

    def  _compile_syllable_regexps(self):
        # should only be letters, but better quote_meta anyway
        quoted_cons = [re.escape(c) for c in self.phones['consonant']]
        quoted_vow = [re.escape(c) for c in self.phones['vowel']]
        quoted_legal = [re.escape(c) for c in self.phones['legal']]
        cons = u'|'.join(quoted_cons)
        vow = u'|'.join(quoted_vow)
        #cons = u'|'.join(self.phones['consonant'])
        #vow = u'|'.join(self.phones['vowel'])
        MAX_ONSET = 20
        legal_cons=[""]*MAX_ONSET

        #make regexp from legal onsets
        #for l in self.phones['legal']:
        for l in quoted_legal:
            if legal_cons[len(l)] == "":
                legal_cons[len(l)]=  l
            else:
                legal_cons[len(l)]= legal_cons[len(l)]+'|' + l 
        
        regexps = []
        # legality principle with max onset
        for i in range(len(legal_cons)-1, 0, -1):
            if len(legal_cons[i]) > 0:
                #regexps.append(re.compile('((?:%s) (?:%s|\s)*)((?:%s) (?:%s))'% (vow,cons,legal_cons[i],vow), re.UNICODE)) # max onset for frequent legal
                regexps.append(re.compile('((?:%s) (?:%s|\s)*) ((?:%s) (?:%s))'% (vow,cons,legal_cons[i],vow), re.UNICODE)) # max onset for frequent legal       
        #defaults
        # V.CV
        regexps.append(re.compile('(%s) ((?:%s) (?:%s))'% (vow, cons, vow), re.UNICODE))
        # VC+.CV
        regexps.append(re.compile('((?:%s) (?:%s|\s)+) ((?:%s) (?:%s))'% (vow,cons,cons,vow), re.UNICODE)) # at least one consonant before 
        #for r in regexps:
        #    print r.pattern

        # finally hiatus
        for h in self.phones['non_diphthongs']:
            (h1, h2) = h.split()
            regexps.append(re.compile('(%s+) (%s+)'% (h1,h2), re.UNICODE))
          
        return regexps

    
    # TODO: remove hard-coding, morph level?
    def process_utterance(self, utt):
        
        for node in utt.xpath('//token[@token_class=\"word\"]'):
              
            segments = [s.get('text') for s in node.xpath('./segment')]
            if len(segments) == 0:
                continue
            text =  u" ".join(segments).lower()
            syllables = self._syllabify(text)

            # add syllable level between token and letter
            # TODO:  maybe apply Oliver's generic transform
            segments = node.xpath('./segment')
            for s in syllables:
                syl_node = Element('syllable', text=u"".join(s.split(' ')))
                node.add_child(syl_node)
                for p in s.split(' '):
                    phone_node = segments.pop(0)
                    phone_node.getparent().remove(phone_node)
                    syl_node.add_child(phone_node)
                      

        


    def _syllabify(self, word):

        for regex in (self.regexps):
            
            while re.search(regex, word):
                word = re.sub(regex, '\\1 ||| \\2', word)

        # some regexp produces additional space ...
        word = word.replace('  ',' ')

        return word.split(' ||| ')
        




