#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

import os
import sys
from shutil import ignore_patterns, copytree, rmtree
import glob

from naive.naive_util import *
from Utterance import *
from processors.UtteranceProcessor import *
from Corpus import *

import default.fnames as fname
import default.const as const

from Resources import *
import default.const as c

import multiprocessing

global debug
debug = False

from configobj import ConfigObjError

class Voice(object):

    ## OSW: new, stricter interface -- not subclass of configuredcomp any more
    def __init__(self, speaker, language, configuration, run_mode, DIRS, clear_old_data=False, max_cores=None):

        self.speaker = speaker
        self.language = language
        self.configuration = configuration
        self.run_mode = run_mode
        self.clear_old_data = clear_old_data
        
        # Using all available CPU cores unless defined otherwise
        if max_cores is not None and max_cores.isdigit():
            self.max_cores = int(max_cores)
        else:
            self.max_cores = multiprocessing.cpu_count()


        # ANT: moved most things to Resources object
        self.res = Resources(speaker=speaker, language=language, configuration=configuration, DIRS=DIRS)        
        
        self.recipe_file = os.path.join(DIRS['CONFIG'], configuration + '.cfg')
        
        train_dir = self.res.path[c.TRAIN]
        voice_dir = self.res.path[c.VOICE]
        train_proc = os.path.join(train_dir, const.PROCESSOR)
        
        print train_dir
        print voice_dir

        if not os.path.isdir(train_proc):
            os.makedirs(train_proc)

        ## Setting this to true stores a version of XML for synthesised utterances after each 
        ## processor is applied, and also a graphic in PDF format:
        self.make_archive = False 
        
        ## voice_config_file will exist after a voice has been trained and saved:
        self.voice_config_file = os.path.join(voice_dir, fname.VOICE_CONF) 
        
        ## Does a trained config already exist for this voice? Treat as trained if so:-
        if os.path.isfile(self.voice_config_file) and not clear_old_data:
            self.trained = self.res.voice_trained = True
        else:
            self.trained = self.res.voice_trained = False
        
        
        if self.run_mode == 'runtime':
            if not self.trained:
                sys.exit('No voice of specified configuration exists to synthesise from')
            
        if self.trained:
            load_from_file = self.voice_config_file
        else:
            assert os.path.isfile(self.recipe_file),"Recipe file %s must exist to train a voice from scratch for requested configuration"%(self.recipe_file)
            load_from_file = self.recipe_file
        


        print 'try loading config from python...'
        print load_from_file

        self.config = {}
        execfile(load_from_file, self.config)
        del self.config['__builtins__']
        print self.config
        # main_work(config)


        print self.run_mode
        ## Check run mode is ok (TODO: assert run_mode isn't "train" if self.trained?):
        if not self.run_mode or not self.config.has_key(self.run_mode + '_stages'):
            print "ERROR: called with mode '%s', but '%s_stages' is not defined in the config file."%(self.run_mode,self.run_mode)
            sys.exit(1)
        

    #     ## Actually load config:
    #     print "Load voice from %s ..."%(load_from_file)          
    #     try:
    #         self.config = ConfigObj(load_from_file, encoding='UTF8', interpolation="Template")
    #     except (ConfigObjError, IOError), e:
    #         sys.exit('Could not read "%s": %s' % (load_from_file, e))


    #     ### -------- load processors ------------
        
    #     self.processors = []
    #     self.config[self.run_mode].walk(self._load_item, call_on_sections=False)

        




    # # recursively traverse configuration recipe to load processors of current mode
    # #
    # def _load_item(self, section, key):
    #     if key=="stages":
    #         if isinstance(section[key], list):
    #             for stage in section[key]:
    #                 self.config[stage].walk(self._load_item, call_on_sections=False)
    #         else: self.config[section[key]].walk(self._load_item, call_on_sections=False)
   
    #     elif key=="processors":
    #         if isinstance(section[key], list):
    #             for proc_name in section[key]:
    #                self.load_processor(proc_name)
    #         else: self.load_processor(section[key])
            
    #     elif key=="resources":
    #         if isinstance(section[key], list):
    #             for resource_name in section[key]:
    #                 self.load_resource(resource_name)
    #         else: self.load_resource(section[key])



    # def load_processor(self, proc_name):  ## , model=False):        
    #     """
    #     Check processor exists and can be loaded. If all OK, add to end of self.processors
    #     """
    #     print "    *** voice loading processor %s ***"%(proc_name)


    #     assert proc_name in self.config,'%s doesn\'t have proc_name in config'%proc_name
    #     processor_config = ConfigObj()
    #     processor_config.update(self.config[proc_name])


### --------------------------------------------------------------------------------
### OSW: I previously removed the possibility of naming a processor after its class
### and having it use default configs, but this should be reinstated...
### --------------------------------------------------------------------------------
### Don't allow proc name to be the name of its class: want to keep
### the style consistent, but consistently using class name as processor name
### means we can not have 2 processors of the same class in the pipeline.
### An example of this is a decision tree for pauses and prominence, or
### a VSM for letters and words.
#         if not isinstance(processor_config, basestring):                
#             if not 'object_class' in processor_config:
#                 if not '.' in proc_name:
#                     oclas = proc_name + '.' + proc_name
#                 else: oclas = proc_name
#                 
#                 processor_config['object_class'] = oclas
### --------------------------------------------------------------------------------   

        # class_string = processor_config['class']
        
        # ## Need to get from string to class name, and import class definition:
        # ClassName = dynamic_load_object(class_string)  ## , model=model)
        
        # ## TODO: Is there a better way to do this? One might be a mapping like:
        # ## mapping = {'NaiveTokeniser.NaiveTokeniser': NaiveTokeniser.NaiveTokeniser}
        
        # processor = ClassName(proc_name, processor_config, self.res) #, self.shared_models)            

        






        self.processors = []

        for stage in self.config[self.run_mode + '_stages']:
            #print [stage]
            #if stage not in self.config:
            #    sys.exit('Stage "%s" not defined in config file'%(stage))
            self.processors.extend(stage)


        ## Fix a few other things -- where is the right place to do this?
        seen_names = []
        for processor in self.processors:
            if not hasattr(processor, "language"):
                processor.language = self.language ## osw TODO: Right place to set this?
            if self.clear_old_data:
                # make sure it's not marked as trained
                processor.trained = False
            if processor.processor_name in seen_names:
                sys.exit('Configuration contains multiple processors with name: "%s"'%(processor.processor_name))
            seen_names.append(processor.processor_name)

            processor.verify(self.res)
    


        #sys.exit('aiucaeuivaoeihv')

        

    def set_mode(self, run_mode):
        assert run_mode in ["train", "runtime"]
        self.run_mode = run_mode
            
    def archive_utterances(self):
        self.make_archive = True

    def synth_utterance(self, input_string, output_wavefile=None, output_labfile=None, basename=None, input_wavefile=None, output_uttfile=None, output_extensions=[]):
    
        output_location = self.res.make_dir(c.VOICE, "output")
        test_utterance_location = self.res.make_dir(c.VOICE, "output/utt")
        test_utterance_name = "temp" 
        
        utt = Utterance(input_string, utterance_location=test_utterance_location)        
        utt.set("utterance_name", test_utterance_name)
        if basename:
            utt.set("utterance_name", basename)    
        ## For synthesis with natural durations:    
        if input_wavefile:
            assert os.path.isfile(input_wavefile)
            utt.set("waveform", input_wavefile)        

        ## clear up previous test synthesis:
#        utterance_path = os.path.join(test_utterance_location, test_utterance_name)
#        if os.path.isfile(utterance_path):
#            os.remove(utterance_path)        
        ## Do it like to remove ALL old files (including cmp etc in case of using natural durations...)
        old_files = glob.glob(output_location + '/*/' + test_utterance_name + '.*')
        for fname in old_files:
            os.remove(fname)
        ## ---------------------------------
        i = 1       
        if self.make_archive:
            utt.archive()
        for processor in self.processors:
            print "\n==  proc no. %s (%s)  =="%(i, processor.processor_name)
            #print " == Before:"
            #utt.pretty_print()
            processor.apply_to_utt(utt, voice_mode=self.run_mode)  ## utt is changed in place

            #print " == After:"
            if self.make_archive:
                utt.archive()
            #utt.pretty_print()            
            i += 1
        #utt.pretty_print()  
        ## Save wave to named file?
        if output_wavefile:
            if not utt.has_external_data("wav"):
                print "Warning: no wave produced for this utt"
            else:
                temp_wave = utt.get_filename("wav")  

                ## Check files are different; realpath so that e.g. / and // are equivalent: 
                if os.path.realpath(temp_wave) != os.path.realpath(output_wavefile):  
                    shutil.copyfile(temp_wave, output_wavefile) 
                    
        if output_labfile:
            if not utt.has_external_data("lab"):
                print "Warning: no lab produced for this utt"
            else:
                temp_lab = utt.get_filename("lab")            
                shutil.copyfile(temp_lab, output_labfile) 

        if output_extensions != []:
            for ext in output_extensions:
                if not utt.has_external_data(ext):
                    print "Warning: no %s produced for this utt"%(ext)
                else:
                    assert output_wavefile
                    output_file = re.sub('wav\Z', ext, output_wavefile)
                    temp_file = utt.get_filename(ext)            
                    shutil.copyfile(temp_file, output_file) 
            

        utt.save()

        if output_uttfile:
            utterance_path = os.path.join(test_utterance_location, test_utterance_name + '.utt')
            shutil.copyfile(utterance_path, output_uttfile)




    def train(self, corpus): 

        if self.trained:
            sys.exit('A trained voice exists for this language/speaker/recipe combination.')

        ## For a while, all_corpus included both text and speech-and-text utterances,
        ## but this has been reverted to original set-up, text_corpus has been restored 
        ## to train calls at positional (not kw as before) arg:
        #all_corpus = corpus.make_utterances(self.res.make_dir(c.TRAIN, "utt"), \
        #                                                clear_old_data=self.clear_old_data)
        speech_corpus = corpus.make_utterances(self.res.make_dir(c.TRAIN, "utt"), \
                                                    clear_old_data=self.clear_old_data)
        text_corpus = corpus.all_text_files()
        
        ## tmporary fix for error:
        '''
        Traceback (most recent call last):
          File "./scripts/train.py", line 115, in <module>
            main_work()
          File "./scripts/train.py", line 110, in main_work
            voice.train(corpus)
          File "/afs/inf.ed.ac.uk/group/cstr/projects/simple4all_2/alessandra_dissertation/tool/Ossian/scripts/main/Voice.py", line 291, in train
            result = pool.apply_async(processor, args=(utterance_file, self.res.make_dir(c.TRAIN, "utt"), self.run_mode))
          File "<string>", line 2, in apply_async
          File "/afs/inf.ed.ac.uk/user/o/owatts/tool/python/ActivePython-2.7/lib/python2.7/multiprocessing/managers.py", line 763, in _callmethod
            conn.send((self._id, methodname, args, kwds))
        cPickle.PicklingError: Can't pickle <type '_sre.SRE_Match'>: attribute lookup _sre.SRE_Match failed
        '''
        unparallelisable_classes = ['BasicStanfordCoreNLP', 'Lexicon'] ## lexicon parallelises very slowly --
                                ## see: http://stackoverflow.com/questions/20727375/multiprocessing-pool-slower-than-just-using-ordinary-functions
        ### ^---- TODO: this is now unsed


        i = 1
        for processor in self.processors:
            #print processor
            #print dir(processor)
            #print type(processor)
            print "\n\n== Train voice (proc no. %s (%s))  =="%(i, processor.processor_name)

            if not processor.trained:  
                ## has a suitable component already been trained?
                if os.path.isdir(processor.component_path):
                    print "Copy existing component for processor " + processor.processor_name                    
                    processor.reuse_component(self.res)
                else:
                    print "Train processor " + processor.processor_name
                    processor.train(speech_corpus, text_corpus)
                        
            print "          Applying processor " + processor.processor_name
            if self.max_cores > 1: pool = multiprocessing.Manager().Pool(self.max_cores)
            for utterance_file in speech_corpus:                
                if self.max_cores > 1 and processor.parallelisable:
                        result = pool.apply_async(processor, args=(utterance_file, self.res.make_dir(c.TRAIN, "utt"), self.run_mode))                        
                else:
                    utterance = Utterance(utterance_file, utterance_location=self.res.make_dir(c.TRAIN, "utt"))
                    processor.apply_to_utt(utterance, voice_mode=self.run_mode)
                    utterance.save()
    #               utterance.pretty_print()
            if self.max_cores > 1:
                pool.close()
                pool.join()
            i += 1
        self.save()


    def save(self):
        """
        Copy the minimal files necessary for synthesis with the built voice to the 
        ``$OSSIAN/voices/`` directory, including a copy of the voice config file.
        This means the config can be tweaked after training 
        without altering the recipe for voices built in the future.
        Also the recipe config can be modified for building future voices without breaking
        already-trained ones.
        """
        # The processor specific files we need are at train/processors/<NAME>/*, excluding the
        # training/ directory.
        
        old = os.path.join(self.res.path[c.TRAIN], 'processors')
        new = os.path.join(self.res.path[c.VOICE], 'processors')
        if os.path.isdir(new):
            rmtree(new)  ## make sure there is nothing there.
        copytree(old, new)
            
        ## Make directory in which synthesis output will be put:
        gendir = os.path.join(self.res.path[c.VOICE], 'output')
        if not os.path.isdir(gendir):
            os.mkdir(gendir)
            
        ## remove the temporary training data from final voice ("ignore" kwarg to copytree
        ## should be used for this -- would't cooperate):
        for tempdir in glob.glob(new + '/*/training/'):
            shutil.rmtree(tempdir)
        
        ## remove processor directories that are now empty -- this is the case if there
        ## was only temporary training data there:
        for proc_dir in glob.glob(new + '/*/'):
            if not os.listdir(proc_dir):
                shutil.rmtree(proc_dir)
        
        ## write config from which voice will be loaded in future:
        filename = self.voice_config_file  
        shutil.copy(self.recipe_file, filename)

#        print self.config
#        self.config.write()
#        print 'TODO: save config'       
        


## helper function -- where does this belong?
# def dynamic_load_object(name):
#     ## see http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
#     proc_or_res = 'processors.'
#     print name, '---'
#     #sys.exit(1)
#     if "." in name:
#         # ANT: scope to configs
#         fullname = proc_or_res + name
#         parts = fullname.split('.')
#         module = ".".join(parts[:-1])
#         #print module
#         #sys.exit(1)
#         #m = importlib.import_module('processors.'+module, 'processors')
#         m = __import__(module )          
#         for comp in parts[1:]:
#             m = getattr(m, comp)            
#         return m
#     else:
#         ## Assume in current scope: 
#         print globals()       
#         return globals()[name] 
