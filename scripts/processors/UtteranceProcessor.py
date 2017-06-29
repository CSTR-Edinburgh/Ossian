#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi


import os
import copy
import glob
import string
from naive.naive_util import *
#from main.VoiceElements import ConfiguredComponent, load_configured_component, dynamic_load_object
#from main.CharacterTable import *
from main.Utterance import *
import lxml
import shutil
import default.const as c

from lxml.html import fromstring

class UtteranceProcessor(object):
    
    def __init__(self, processor_name, config, voice_resources): # , shared_models):
        '''
        Initialise from ConfigObj, not config file. No validation/type conversion
        is now done with configobj and validate modules -- instead, each class
        definition should check and convert the configs required by it, and it
        is also up to the class definition to provide defaults if necessary. By
        convention, all config values will be added as instance attributes. 
        '''

        self.processor_name = processor_name
        self.trained = False
#        self.shared_models = shared_models
        assert isinstance(config, ConfigObj)
        self.config = ConfigObj(config, encoding='UTF8', interpolation="Template")
        self.my_model = self.config.get('model_to_use', None) ## should there be a class of processor forced to use a model? 
        
        ## name of attribute at utt root node, used as condition of processing:
        self.apply_to_utts_which_have = self.config.get('apply_to_utts_which_have', 'waveform')
        self.train_on_utts_which_have = self.config.get('train_on_utts_which_have', 'waveform')
        
        self.voice_resources = voice_resources
        
        self.component_path = ''  ## will be set by subclasses to the location of suitable trained 
                                  ## models (if they have been trained)
        self.load()  ## this method should be provided by subclasses to do 
                     ## class-specific things after intantiation
        
        
    def load(self):
        '''
        Subclasses should provide this method to do class-specific things 
        after instantiation.
        This includes setting default values of required instance attributes, and
        reading new values for them from config, converting type as necessary. 
        '''
        ## example of getting attribute from config, converting type and giving default:
        self.i = int(self.config.get('arbitrary_int', 5)) 
        
        raise NotImplementedError, "load() method should be provided by subclass '%s'"%(self.__class__)
    
    
    def apply_to_utt(self, utterance, voice_mode="runtime", save=False):

        if not voice_mode=='runtime':
            if not utterance.get(self.apply_to_utts_which_have):
                print "s",
                return
            ## self.apply_to_utts_which_have

        ## Make utterance processors_used attribute if necessary. [Add on utterance creation?]
        if not utterance.has_attribute("processors_used"):
            utterance.set("processors_used", "" )
        ## check this processor hasn't already been used on utt:
        proc_used = utterance.get("processors_used").split(",")
        if self.processor_name in proc_used:
            print "u",
            return  ## don't do anything
        
        if utterance.get("status") != "OK":
            print "-",
            return

        ## Add the name of the processor to the utt -- don't apply a processor 2ce:
        utterance.set("processors_used", utterance.get("processors_used") + "," + self.processor_name)
        print "p",        
        self.process_utterance(utterance)
        if save: utterance.save()


    def process_utterance(self, utterance):
        ## Work to be performed on an utterance should be put here in subclasses
        pass

    def train(self, corpus, text_corpus):
        '''
        Inherited method to do processor training. This just makes utterance objects from
        the XML files of the corpus, and filters the utterances in the
        corpus to find the ones this processor is configured to train on, and which have
        not been flagged as bad (status != OK).
        
        The actual processor-specific work should be subclassed in do_training
        '''

        corpus = [Utterance(fname) for fname in corpus]
        
        corpus = [utt for utt in corpus if utt.get(self.train_on_utts_which_have)]

        corpus = [utt for utt in corpus if utt.get('status') == 'OK']
        self.do_training(corpus, text_corpus)
    
    def do_training(self, subcorpus, text_corpus):
        """
        This method can be provided in subclasses which require training to specify what is 
        actually done -- relevant utterances already selected by train method.
        """
        print "          (This processor requires no training)"
        self.config["is_trained"] = True

    def get_location(self):
        """
        Get the directory where processor data is/has been stored, based on processor name
        and voice resources
        """
        name = self.processor_name
        if self.voice_resources.voice_trained:
            return self.voice_resources.get_dirname(name, c.VOICE, subtype=c.PROCESSOR)
        else:
            return self.voice_resources.get_dirname(name, c.TRAIN, subtype=c.PROCESSOR)

    def get_training_dir(self):
        """
        Get the subdirectory of the processor directory where temporary training files 
        will be written. Make the dir if it doesn't already exist.
        
        TODO: make 'training' not hardcoded.
        """
        training = os.path.join(self.get_location(), 'training')
        if not os.path.isdir(training):
            os.makedirs(training)
        return training
        
    def reuse_component(self):
        assert self.component_path != ''
        model_location = self.get_location()
        shutil.rmtree(model_location)  
        shutil.copytree(self.component_path, model_location)
        self.load()
        
    def __call__(self, utterance_file, utterance_location, mode):
        utterance = Utterance(utterance_file, utterance_location=utterance_location)
    
        return self.apply_to_utt(utterance, voice_mode=mode, save=True)



class SUtteranceProcessor(object):
    
    def __init__(self):

        self.trained = False
        self.parallelisable = True
        self.component_path = ''  ## will be set by subclasses to the location of suitable trained 
        
        ## name of attribute at utt root node, used as condition of processing:
        self.apply_to_utts_which_have = 'waveform' # self.config.get('apply_to_utts_which_have', 'waveform')
        self.train_on_utts_which_have = 'waveform' # self.config.get('train_on_utts_which_have', 'waveform')
        
        # self.voice_resources = voice_resources
        
        #                           ## models (if they have been trained)
        # self.load()  ## this method should be provided by subclasses to do 
        #              ## class-specific things after intantiation
        
    def verify(self, voice_resources):    
        '''
        Link up voice resources, pointing to all external resources, physical locations on disk, etc. 
        Subclasses can add to this to check if an object is trained etc.
        '''    
        self.voice_resources = voice_resources


    # def load(self):
    #     '''
    #     Subclasses should provide this method to do class-specific things 
    #     after instantiation.
    #     This includes setting default values of required instance attributes, and
    #     reading new values for them from config, converting type as necessary. 
    #     '''
    #     ## example of getting attribute from config, converting type and giving default:
    #     self.i = int(self.config.get('arbitrary_int', 5)) 
        
    #     raise NotImplementedError, "load() method should be provided by subclass '%s'"%(self.__class__)
    
    
    def apply_to_utt(self, utterance, voice_mode="runtime", save=False):

        if not voice_mode=='runtime':
            if not utterance.get(self.apply_to_utts_which_have):
                print "s",
                return
            ## self.apply_to_utts_which_have

        ## Make utterance processors_used attribute if necessary. [Add on utterance creation?]
        if not utterance.has_attribute("processors_used"):
            utterance.set("processors_used", "" )
        ## check this processor hasn't already been used on utt:
        proc_used = utterance.get("processors_used").split(",")
        if self.processor_name in proc_used:
            print "u",
            return  ## don't do anything
        
        if utterance.get("status") != "OK":
            print "-",
            return

        ## Add the name of the processor to the utt -- don't apply a processor 2ce:
        utterance.set("processors_used", utterance.get("processors_used") + "," + self.processor_name)
        print "p",        
        self.process_utterance(utterance)
        if save: utterance.save()


    def process_utterance(self, utterance):
        ## Work to be performed on an utterance should be put here in subclasses
        pass

    def train(self, corpus, text_corpus):
        '''
        Inherited method to do processor training. This just makes utterance objects from
        the XML files of the corpus, and filters the utterances in the
        corpus to find the ones this processor is configured to train on, and which have
        not been flagged as bad (status != OK).
        
        The actual processor-specific work should be subclassed in do_training
        '''

        corpus = [Utterance(fname) for fname in corpus]
        
        corpus = [utt for utt in corpus if utt.get(self.train_on_utts_which_have)]

        corpus = [utt for utt in corpus if utt.get('status') == 'OK']
        self.do_training(corpus, text_corpus)
    
    def do_training(self, subcorpus, text_corpus):
        """
        This method can be provided in subclasses which require training to specify what is 
        actually done -- relevant utterances already selected by train method.
        """
        print "          (This processor requires no training)"
        self.is_trained = True

    def get_location(self):
        """
        Get the directory where processor data is/has been stored, based on processor name
        and voice resources
        """
        name = self.processor_name
        if self.voice_resources.voice_trained:
            return self.voice_resources.get_dirname(name, c.VOICE, subtype=c.PROCESSOR)
        else:
            return self.voice_resources.get_dirname(name, c.TRAIN, subtype=c.PROCESSOR)

    def get_training_dir(self):
        """
        Get the subdirectory of the processor directory where temporary training files 
        will be written. Make the dir if it doesn't already exist.
        
        TODO: make 'training' not hardcoded.
        """
        training = os.path.join(self.get_location(), 'training')
        if not os.path.isdir(training):
            os.makedirs(training)
        return training
        
    def reuse_component(self, voice_resources):
        assert self.component_path != ''
        model_location = self.get_location()
        shutil.rmtree(model_location)  
        shutil.copytree(self.component_path, model_location)
        self.verify(voice_resources)
        
    def __call__(self, utterance_file, utterance_location, mode):
        utterance = Utterance(utterance_file, utterance_location=utterance_location)
    
        return self.apply_to_utt(utterance, voice_mode=mode, save=True)
