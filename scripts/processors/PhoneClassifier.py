#!/usr/bin/env python
# -*- coding: utf-8 -*-

## TODO: utterance.xpath uses hardcoded xpaths through out...

from UtteranceProcessor import *
import logging
import os
import re
import default.const as c
import unicodedata
from math import log
from configobj import ConfigObj
from BasicTokenisers import RegexClassifier
from collections import defaultdict

class PhoneClassifier(UtteranceProcessor):
    


    def load(self):
        self.target_nodes = self.config.get('target_nodes', '//token')
        self.input_attribute = self.config.get('input_attribute', 'text')

        ## osw: For now, store phone class info to voice, not corpus.
        #self.phone_class_file = os.path.join(self.voice_resources.get_path(c.LANG), self.config['phone_classes'])
        self.phone_class_file = os.path.join(self.get_location(), self.config['phone_classes'])
        
        self.trained = False
        if os.path.isfile(self.phone_class_file):
            self.trained = True
        self.phone_classes = ConfigObj(self.phone_class_file, encoding='utf8')
        #if self.trained == False:
        #    self.phone_classes.clear()
        
        pass

    def do_training(self,speech_corpus,text_corpus):

        if self.trained == True:
            return
        tokens = []
        
        for utterance in speech_corpus:
            for node in utterance.xpath('//token[@token_class=\"word\"]'):
                segments = [s.get('text') for s in node.xpath('./segment')]
                
                if len(segments) > 0 and segments[0] is not None:
                    token = [c.lower() for c in segments]
                    tokens.append(token)

            
        # guess vowels and consonats
        letter_bigrams = self._get_ngrams(tokens, 2, '_')
        letter_unigrams = self._get_ngrams(tokens, 1, '_')
        
        vowels = self._sukhotin_vowels(letter_unigrams, letter_bigrams)

        
        consonants = []
        for l in letter_unigrams:
            if l not in vowels:
                consonants.append(l)

        # get legal consonant clusters of onsets and codas
        quoted_cons = [re.escape(c) for c in consonants]
        cons = u"|".join(quoted_cons)
        print cons
        legal_onsets =self._legal(tokens, '((?:%s|\s)+).*' %cons)
        legal_codas = self._legal(tokens, '.*?((%s|\s)+)$' %cons)

        
        
        # guess which vowel letter sequences don not form diphthongs
        hiatus = self._get_mayer_hiatus(tokens, vowels, 0.5)
        
        # write classes
        self.phone_classes['vowel'] = vowels
        self.phone_classes['consonant'] = consonants
        #self.phone_classes['diphthongs'] = diphthongs.keys()
        self.phone_classes['non_diphthongs'] = hiatus.keys()
        self.phone_classes['legal'] = legal_onsets.keys()
        self.phone_classes.write()
        
        #raw_input()
        self.trained = True



    def process_utterance(self, utt):

        for l in utt.xpath("//segment[@text]"):
            if l.get("text").lower() in self.phone_classes['vowel']:
                l.set("pclass", "v")
            else:
                l.set("pclass", "c")
            

        




    def _sukhotin_vowels(self, unigrams, bigrams):
        """
        Sukhotin's algorithm for finding vowels from text.

        Based on two assumptions:
        -The most frequent letter represents a vowel (not always true?)
        -Vowels are more often next to consonants than not (consonant clusters?)
    
        Example results using wikipedia frontpage text:
        Finnish  -- vowels:ieauäoyö   consonants:dcbgfhkjmlnpsrtwv
        English  -- vowels:eiaou      consonants:cbdgfhkjmlnqpsrtwvyxz
        Spanish  -- vowels:iaeouéáíóú consonants:msqřcbdgfhkjlnñprtwvyxzü
        Romanian -- vowels:ieaouăâéü  consonants:șțîōcbdgfhkjmlnpsrtwvyxz
    
        """

        rowsums = {}
        for u in unigrams:
            rowsums[u] = 0
            for b in bigrams:
                if b[0]!= b[1]: #diagonal zero
                    if b[0] == u or b[1] == u:
                        rowsums[u]+= bigrams[b] 
        vowels = []
        while (True):
            # largest rowsum > 0 is vowel
            v = max(rowsums, key=rowsums.get)
            if (rowsums[v]) <= 3:
                break
            if v != "_":
                vowels.append(v)
            #print v, rowsums[v], unigrams[v]
            rowsums[v] = 0

            # substract co-occurances with the new-found vowel
            for b in bigrams:
                if b[0] != b[1]:
                    if (b[0] == v and b[1] not in vowels):
                        rowsums[b[1]] -= bigrams[b]*2.0
                    elif (b[1] == v and b[0] not in vowels):
                        rowsums[b[0]] -= bigrams[b]*2.0
        return vowels


    def _get_mayer_hiatus(self, tokens, vowels, thresh):
        MIN_THRESH = 0.01
        adjacent = defaultdict(int)
        separated = defaultdict(int)
        for t in tokens:
            for i in range(len(t)-1):
                if t[i] in vowels:
                    if t[i+1] in vowels:
                        adjacent[t[i]+" "+t[i+1]]+=1
                    if i < len(t)-2 and t[i+2] in vowels:
                        separated[t[i]+" "+t[i+2]]+=1
        ratio = {}
        dip = {}
        N = float(sum(adjacent.values()))
        for pair in adjacent.keys():
            if adjacent[pair] / N > MIN_THRESH:
                ratio = adjacent[pair] / float(separated[pair]+1)
                if ratio < thresh:
                    dip[pair] = ratio


        return dip


  
    def _legal(self,tokens, legal_re_str):
        
        legal = defaultdict(int)
        legal_re = re.compile(legal_re_str, re.UNICODE)

        for t in tokens:
            t = u" ".join(t)
            m = legal_re.match(t)
            if m:
                clus = m.groups(0)[0]
                clus = clus.strip()
                clus= u" ".join(clus.split())
                legal[clus] +=1

        count = sum(legal.values())
        for k in legal.keys():
            legal[k] = float(legal[k])/count
            if legal[k]  < 0.01:
                del legal[k]

        return legal


    def _get_ngrams(self, tokens, n, pad = ''):
        ngrams = defaultdict(int)
        for token in tokens:
            if type(token)!=list:
                token = list(token)
            if pad:
                token = [pad]+token+[pad]
                #token = ['_']+token+['_']
        

            for i in range(len(token)-n+1):

                if n > 1:
                    ngram = tuple(token[i:i+n])
             
                else:
                    ngram = token[i]

           
                ngrams[(ngram)] += 1
        

        return ngrams

  



