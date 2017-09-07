#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - June 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

# 
# The processors in this module integrate machine learning models 
# implemented in scikit-learn (http://scikit-learn.org/stable)
# 

import os
import numpy as np
import pickle
from sklearn import tree
from sklearn.feature_extraction import DictVectorizer

from UtteranceProcessor import SUtteranceProcessor
import logging
import default.const as c



class SKLDecisionTree(SUtteranceProcessor):


    def __init__(self, processor_name='decision_tree', target_nodes='', output_attribute='', contexts=[], min_samples_leaf=10):
        
        self.processor_name = processor_name
        self.target_nodes = target_nodes

        self.min_samples_leaf = min_samples_leaf    ## TODO Set other tree building defaults here?

        self.model = None
                 
        ## For now, use context list inside the recipe: 
        if contexts == []:
            sys.exit('config for SKLDecisionTree should contain a list of contexts') 
        self.context_list = contexts             
        
        assert output_attribute != ''
        self.output_attribute = output_attribute

        ## Check response exists in context list, and find its index:
        self.feature_names = [name for (name, xpath) in self.context_list]  
        assert 'response' in self.feature_names
        reponse_index = self.feature_names.index('response')
        
        ## Ensure response is at *start* of context list:
        response = self.context_list[reponse_index]
        del self.context_list[reponse_index]
        self.context_list.insert(0, response)

        super(SKLDecisionTree, self).__init__()

    def verify(self, resources):
        super(SKLDecisionTree, self).verify(resources)

        self.model_file = os.path.join(self.get_location(), "model.pkl") ## TODO: standard filename in const.py?
        
        if os.path.isfile(self.model_file):
        
            ## If the model file exists, count it as trained -- get everything from processor dir:
            f = open(self.model_file, 'rb')
            [self.x_vectoriser, self.y_vectoriser, self.model] = pickle.load(f)
            f.close()              



    def process_utterance(self, utt):
        
        assert self.model, 'Cannot apply processor %s until its model is trained'%(self.processor_name)

      
        for node in utt.xpath(self.target_nodes):
                   
            input_features = dict(node.get_context_vector(self.context_list))
            input_features = self.x_vectoriser.transform(input_features).toarray()
             ## no need to remove response -- will be ignored if not in x_vectoriser

            decision = self.model.predict(input_features)
            
            ### Skip this -- assume response is numeric:
            #decision = self.y_vectoriser.inverse_transform(decision) 

            '''
            ##PROBLEM: 0 values not put in inverse transformed dict:
            >>> print yv.inverse_transform(yv.transform([{'response': 3}]))
            [{'response': 3.0}]
            >>> print yv.inverse_transform(yv.transform([{'response': 0.0}]))
            [{}]
            '''
            
            decision = decision[0] ## prediction is a list of 1 int

            # prososdy labeling is numeric but quantized for HTS. so 2.0 != 2 for contextual features
            # does this break other modules?
            try:
                if decision == int(decision):
                    decision = int(decision)
            except:
                pass

            node.set(self.output_attribute, unicode(decision)) 
                        ## TODO: where is best place to convert to unicode?


    def do_training(self, speech_corpus, text_corpus):
        
        if self.model:  ## if already trained...
            return

        ## 1) get data:
        #### [Added dump_features method to Utterance class, use that: ]
        x_data = []
        y_data = []
        for utterance in speech_corpus:
            
            utt_feats = utterance.dump_features(self.target_nodes, \
                                                self.context_list, return_dict=True)

            for example in utt_feats:
                assert 'response' in example,example
                y_data.append({'response': example['response']})
                del example['response']
                x_data.append(example)
        
        ## Handle categorical features (strings) but to keep numerical ones 
        ## as they are:
        
        x_vectoriser = DictVectorizer()
        x_data = x_vectoriser.fit_transform(x_data).toarray()
        
        y_vectoriser = DictVectorizer()
        y_data = y_vectoriser.fit_transform(y_data).toarray()
      
        if False:
            print x_data
            print y_data
        
        ## 2) train classifier:
        model = tree.DecisionTreeClassifier(min_samples_leaf=self.min_samples_leaf)

        model.fit(x_data, y_data) 
        print '\n Trained classifier: '
        print model
        print '\n Trained x vectoriser:'
        print x_vectoriser
        print 'Feature names:'
        print x_vectoriser.get_feature_names()
        print '\n Trained y vectoriser:'
        print y_vectoriser
        print 'Feature names:'
        print y_vectoriser.get_feature_names()
        
        ## 3) Save classifier by pickling:
        output = open(self.model_file, 'wb')
        pickle.dump([x_vectoriser, y_vectoriser, model], output)
        output.close()        
        
        ## Write ASCII tree representation (which can be plotted):
        tree.export_graphviz(model, out_file=self.model_file + '.dot',  \
                                     feature_names=x_vectoriser.get_feature_names())
        
        self.verify(self.voice_resources) # ## reload -- get self.model etc


class SKLDecisionTreePausePredictor(SKLDecisionTree):

    ## TODO: revise this -- all hardcoded!

    def process_utterance(self, utt):
        ## add predictions at token level:
        super(SKLDecisionTreePausePredictor, self).process_utterance(utt)  ##

        ## assume if there is a waveform attached, we are training, otherwise runtime:
        is_train_time = ('waveform' in utt.attrib)

        ## act on predictions by adding silence symbol:
        for segment in utt.xpath('//segment'):
            ## if we are at run time and end of sentence, always add silence
            token_text = segment.xpath('ancestor::token/attribute::text')
            end_of_sentence = (token_text == '_END_')
            if (not is_train_time) and end_of_sentence:
                segment.attrib['pronunciation'] = 'sil'
            elif segment.get('pronunciation') in [c.POSS_PAUSE, c.PROB_PAUSE]:
                silence_predicted = '0'
                for ancestor in segment.iterancestors():
                    if ancestor.has_attribute(self.output_attribute):
                        silence_predicted = ancestor.get(self.output_attribute)
                if silence_predicted=='1':
                    segment.attrib['pronunciation'] = 'sil'
                else:
                    segment.getparent().remove(segment)  ## remove the segment altogether