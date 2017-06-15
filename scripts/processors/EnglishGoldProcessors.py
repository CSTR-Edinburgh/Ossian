#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - August 2014 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk

import sys
import os
import subprocess
import default.const as c
import regex
import copy

from processors.UtteranceProcessor import UtteranceProcessor
from processors.NodeEnricher import NodeEnricher
from main.Utterance import Element

from util.NodeProcessors import ensure_times_consistent

from naive.naive_util import writelist

class EnglishTextNormaliser(NodeEnricher):
    '''
    '''
    def load(self):
        NodeEnricher.load(self)

        self.target_nodes = self.config.get('target_nodes', '//utt')
        self.input_attribute = self.config.get('input_attribute', 'text')      
        self.output_attribute = self.config.get('output_attribute', 'norm_text')
        
        self.scripts = os.path.join(self.voice_resources.get_path(c.RULES), 'textnorm', 'scripts')
        self.rules = os.path.join(self.voice_resources.get_path(c.RULES), 'textnorm', 'rules')
        
        ## TODO: check text norm scripts exist where expected:
        #     . . .
        
    def enriching_function(self, instring):
        
        ## quote the string and escape ' for shell command:
        instring = "'" + instring.replace("'", "'\\''") + "'" 
 
        comm = "echo %s | %s/utf2ascii_puncts.pl | "%(instring, self.scripts)
        comm += " %s/normalize_puncts.pl %s/abbrevlist %s/tldlist | "%(self.scripts, self.rules, self.rules)
        comm += "%s/tokenize_words.pl %s/abbrevmap %s/tldlist %s/hyphenated | "%(self.scripts, self.rules, self.rules, self.rules)
        comm += "%s/numproc -x%s/num_excp"%(self.scripts, self.rules) 

        normalised_string = subprocess.check_output(comm, shell=True)

        ## TODO: handle b.b.c. -> b b c here, and lowercase?
        ## TODO: handle punctuation for incomplet sentences:  Of silence,"/>
        
        return normalised_string.strip(' \n').decode('utf-8')
        
        #     filter_text_gigaword.pl omitted from the start of the pipe: we don't want to pre-filter
        #     text for things that look corrupted, at least in the case of synthesis where everything 
        #     must be handled somehow.
        # 
        #     final_cleanup.pl omitted from the end of the pipeline -- don't want to lowercase or 
        #     discard punctuation, but does this do additional useful things?

    def do_training(self, speech_corpus, text_corpus):
        print "EnglishTextNormliser requires no training"    
        






class BasicStanfordCoreNLP(UtteranceProcessor):
    '''
    Basic version doesn't do anything with coref, const. and depend. parses produced by analysis.
    
    For now, words from all sentences found in the utterance are put at the top level
    of the utterance -- sentences are throw away, but could be used later for e.g.
    paragraph-level utterances. 
    
    If merge_clitics, merge e.g. I 'll -> single word I'll
    
    Add spaces back in where there is no punctuation as points at which silence can
    be inserted during alignment
    
    Add reduced POS as well as Stanford POS
    '''
    def load(self):
    
        self.target_nodes = self.config.get('target_nodes', '//utt')    
        self.input_attribute = self.config.get('input_attribute', 'norm_text')
        
        self.merge_clitics = self.config.get('merge_clitics', 'True') ## string, not bool
    
        ## check tools exist:
        corenlp_location = os.path.join(self.voice_resources.path[c.BIN], '..', \
                                                            'corenlp-python', 'corenlp')
        assert os.path.isdir(corenlp_location)
        sys.path.append(corenlp_location)
        from corenlp import StanfordCoreNLP
        corenlp_dir = os.path.join(corenlp_location, '..', 'stanford-corenlp-full-2014-06-16')
        
        ## Each document is to be treated as one sentence, no sentence splitting at all. 
        ## Write config for this if necessary:
        corenlp_conf_name = 'no_sentence_split.properties'
        corenlp_conf_file = os.path.join(corenlp_location, corenlp_conf_name)
        if not os.path.isfile(corenlp_conf_file):
            data = ['annotators = tokenize, ssplit, pos, lemma, ner, parse, dcoref', \
                    'ssplit.isOneSentence = true']
            writelist(data, corenlp_conf_file)

        print 'Loading stanford corenlp modules from %s ...'%(corenlp_dir)
        print 'Takes a while (~20-30 seconds)...'
        self.models = StanfordCoreNLP(corenlp_dir, properties=corenlp_conf_name)     
                                           

                                                            
    def process_utterance(self, utt):

        ## _END_ node
        end_node = Element('token')
        end_node.set(self.input_attribute, '_END_')
        utt.append(end_node)

        for node in utt.xpath(self.target_nodes):
            
            assert node.has_attribute(self.input_attribute)
            input = node.get(self.input_attribute)
            analysis = self.models.raw_parse(input)
            
            ## analysis looks like this:
            
            #     {'coref': ...
            #      'sentences': [{'parsetree':  ... } 
            #                     'text': 
            #                     'dependencies': 
            #                     'indexeddependencies': 
            #                     'words': [('and', {'NamedEntityTag': 'O', \
            #                         'CharacterOffsetEnd': '3', 'Lemma': 'and', \
            #                         'PartOfSpeech': 'CC', 'CharacterOffsetBegin': '0'}), ... ]
            #                       }
            #                   ]
            #     }
            
            ## preprocess the analysis: add spaces back between words where there is no
            ## punc (to use as potential silence insertion points for alignment), and
            ## possibly merge clitics (he 's -> he's, i ll' -> i'll)
            

            ## MERGE SUCCESSIVE PUNCTUATION TOKENS 
            new_analysis = {}
            new_analysis['sentences'] = []
            for sentence in analysis['sentences']:
                #new_sentence = copy.deepcopy(sentence)
                #new_sentence['words'] = []
                new_words = []
                for word in sentence['words']:
                    # is there a previous word?
                    if len(new_words) > 0:
                        # if both space / punct:
                        if self.all_space_or_punc(new_words[-1][0]) and self.all_space_or_punc(word[0]):
                            prev_word = new_words.pop(-1)
                            combined = self.merge_words(prev_word, word)
                            new_words.append(combined)
                        else:
                            new_words.append(word)
                    else:
                        new_words.append(word)
                sentence['words'] = new_words
                new_analysis['sentences'].append(sentence)
            analysis = new_analysis     


            ## MERGE CLITICS 
            ## This also merges e.g. . ''  -->  .''  (given by norm scripts from   ."  ) at sentence ends.
            if self.merge_clitics == 'True': ## string not bool
                new_analysis = {}
                new_analysis['sentences'] = []
                for sentence in analysis['sentences']:
                    #print sentence
                    new_sentence = copy.deepcopy(sentence)
                    new_sentence['words'] = []
                    i = 0
                    while i < (len(sentence['words'])-1):
                        this_word = sentence['words'][i]
                        next_word = sentence['words'][i+1]
                        if next_word[0].startswith("'") or next_word[0] == "n't":
                            merged = self.merge_words(this_word, next_word)
                            new_sentence['words'].append(merged)
                            i += 2
                        else:
                            new_sentence['words'].append(this_word)
                            i += 1
                    last_word = sentence['words'][-1]
                    if not(last_word[0].startswith("'") or last_word[0] == "n't"):
                        new_sentence['words'].append(last_word)
                    new_analysis['sentences'].append(new_sentence)
                analysis = new_analysis                    
                 
            
            ## ADD SPACES:
            new_analysis = {}
            new_analysis['sentences'] = []
            for sentence in analysis['sentences']:
                new_sentence = copy.deepcopy(sentence)
                new_sentence['words'] = []
                ## For now, ignore parsetree, dependencies, indexeddependencies (sentence level)
                previous_lemma = '_NONE_'
                for word in sentence['words']:
                
                    (text, word_attributes) = word
                    this_lemma = word_attributes['Lemma']
                    
                    ## Add whitespace back in to tokens to use for silence insertion in alignment later.
                    ## Don't add it where either neighbour is punctuation, or at start of 
                    ## utt (where previous_lemma is '_NONE_':
                    if not (self.all_space_or_punc(previous_lemma) or \
                                                self.all_space_or_punc(this_lemma)):   
                        if previous_lemma != '_NONE_':                     
                            new_sentence['words'].append((' ', {'NamedEntityTag': ' ', \
                                                        'PartOfSpeech': ' ', 'Lemma': ' '}))
                    previous_lemma = this_lemma
                    new_sentence['words'].append(word)
                new_analysis['sentences'].append(new_sentence)
            analysis = new_analysis
            
            
            ## combine all sentences to one for now:
            all_words = []
            for sentence in analysis['sentences']:
                all_words.extend(sentence['words'])
                
            
            ## Add stuff into the target node (probably utt):
            for word in all_words:
            
                (text, word_attributes) = word
                word_node = Element('token') ## also includes punctuation etc.
                word_node.set(self.input_attribute, text) ## see above at sentence level about 'text'
                
                ## For now, ignore CharacterOffsetBegin, CharacterOffsetEnd (word level)
                word_node.set('ne', word_attributes['NamedEntityTag']) 
                word_node.set('pos', word_attributes['PartOfSpeech']) 
                word_node = self.add_reduced_POS(word_node)
                
                word_node.set('lemma', word_attributes['Lemma']) 
                
                utt.append(word_node)
                
        ## _END_ node
        end_node = Element('token')
        end_node.set(self.input_attribute, '_END_')
        utt.append(end_node)    

    def add_reduced_POS(self, node):
        full_POS = node.attrib['pos']
        if '|' in full_POS:
            full_POS = full_POS.split('|')[0]
    
        ## add coarse POS (content/function) and reduced (adj,noun,adv,etc.)
        map = dict([('IN', 'function'), ('TO', 'function'), ('DT', 'function'), \
                ('PDT', 'function'), ('MD', 'function'), ('CC', 'function'), \
                ('WP', 'function'), ('PP$', 'function'), ('EX', 'function'), \
                ('POS', 'function'), ('PP', 'function'), ('WDT', 'function'), \
                ('PRP', 'function'), ('PRP$', 'function'), ('RP', 'function'), \
                ('WP$', 'function'), ('WRB', 'function'), ('LS', 'function'),\
                ('NN', 'noun'), ('NNS', 'noun'), \
                ('NP', 'noun'), ('NNP', 'noun'), ('NPS', 'noun'), ('NNPS', 'noun'), ('FW', 'noun'), \
                 ('VBG', 'verb'), ('VBN', 'verb'), \
                ('VB', 'verb'), ('VBD', 'verb'), ('VBP', 'verb'), ('VBZ', 'verb'), \
                ('JJ', 'adj'), ('JJR', 'adj'), ('JJS', 'adj'), ('CD', 'adj'), \
                ('RB', 'adv'), ('RBR', 'adv'), ('RBS', 'adv'), ('UH', 'interj')])

                ## NOTE:
                # FW -- foreign word -> noun
                # LS -- list item -> function

        if full_POS not in map:
            if full_POS == ' ':
                red_pos = 'space'
            elif self.all_space_or_punc(full_POS):
                red_pos = 'punc'
            else:
                print 'MISSING POS: %s'%(full_POS)
                red_pos = 'other'
        else:
            red_pos = map[full_POS]
        node.set('coarse_pos', red_pos)
        return node


    

    def all_space_or_punc(self, token):
        '''Use regex to match unicode properties to see if token is all punctuation or space
            This duplicates later work by e.g. token classifier.'''
        space_or_punc = '[\p{Z}||\p{C}||\p{P}||\p{S}]'
        return regex.match('\A' + space_or_punc + '+\Z', token)
        
        
    def merge_words(self, word1, word2):
        merged_form = word1[0] + word2[0]
        merged_POS = word1[1]['PartOfSpeech'] + '|' + word2[1]['PartOfSpeech']
        merged_lemma = word1[1]['Lemma']   ## first word's lemma
        merged_NER = word1[1]['NamedEntityTag']  ## first words NE tag
        merged = (merged_form, \
                    {'PartOfSpeech': merged_POS, \
                    'Lemma': merged_lemma, \
                    'NamedEntityTag': merged_NER})
        return merged
        
        
class EnglishPostlexRules(UtteranceProcessor):
    '''
    Anna 2010 HTS voice in VCTK uses 4 rules:
        --postlex_apos_s_check
        --postlex_intervoc_r
        --postlex_the_vs_thee
        --postlex_a
    The first is handled by our lexicon, as we merge 's to the preceding word.
    This last seems to be to handle letter-name pronunciation of a, ensuring not reduced.
    The other 2 are implemented in this processor. 
    More can be added with extra methods.
    '''
    def load(self):
        
        self.rules_to_apply = self.config.get('rules_to_apply', 'linking_r,the_vs_thee')
        if isinstance(self.rules_to_apply, str):
            self.rules_to_apply = [ self.rules_to_apply ] ## str if only 1 value in config list
        
        for rule in self.rules_to_apply:
            assert rule in ['linking_r', 'the_vs_thee'],'Unknown postlexical rule: %s'%(rule)
            
    def process_utterance(self, utt):
        for rule in self.rules_to_apply:
            if rule == 'linking_r':
                utt = self.linking_r(utt)
            if rule == 'the_vs_thee':
                utt = self.the_vs_thee(utt)
    
    def linking_r(self, utt):
        '''
        Remove r if next segment is not a vowel.
        '''
        previous_segment = None
        for segment in utt.xpath('//segment'):
            if previous_segment != None:
                #print previous_segment
                #print previous_segment.attrib
                if previous_segment.attrib['pronunciation'] == 'r':
                    if 'vowel_cons' in segment.attrib: ## silences etc. might now have this
                        if segment.attrib['vowel_cons'] != 'vowel':
                            ## remove previous segment.
                            previous_segment.getparent().remove(previous_segment) 
            previous_segment = segment
        if utt.has_attribute("waveform"):
            utt = ensure_times_consistent(utt, 'segment')
            utt = ensure_times_consistent(utt, 'state')
        return utt
    
    def the_vs_thee(self, utt):
        ''' int "the", switch schwa -> i if next phone is vowel, and 
            switch i -> schwa if not.
            Combilex-rp entries for the: 
                ("the" (dt full) (((D i) 1)))
                ("the" (dt reduced) (((D @) 0)))
                ("the" (dt reduced) (((D i) 0)))
        Need to rerun phonetic feature added after this to make sure changed phones' features
        still fit.
        '''
        for token in utt.xpath('//token'):
            if token.attrib['norm_text'].lower() == 'the':
                vowel = token.xpath("descendant::segment[@vowel_cons='vowel']")
                if len(vowel) != 1:
                    print 'WARNING: weird number of vowels...' ## do nothing
                else:
                    vowel = vowel[0]
                    following_type = token.xpath("./following::segment[1]/attribute::vowel_cons")
                    if len(following_type) > 0 and following_type[0] == 'vowel':
                        vowel.set('pronunciation', 'i')
                    else:
                        vowel.set('pronunciation', '@')
        return utt
                    
    
