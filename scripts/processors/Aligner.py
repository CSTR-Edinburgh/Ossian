#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

import glob
import shutil
from processors.UtteranceProcessor import SUtteranceProcessor
from util.NodeProcessors import *
#from util.NodeProcessors import add_states_from_label
# from util.Aligner import *
import default.const as c

class SegmentAligner(SUtteranceProcessor):

    def __init__(self, processor_name='aligner', target_nodes='//segment', target_attribute='segment_name', \
                    input_label_filetype='align_lab', acoustic_feature_filetype='cmp', \
                    output_label_filetype='time_lab', silence_symbol='sil', silence_tag='has_silence', min_silence_duration=50, \
                    viterbi_beam_width='', acoustic_subrecipe='standard_alignment', \
                    training_settings={'MIXTURE_SCHEDULE': '0 0 0', 'NREEST': '2'}, n_training_utts=0):
 

# alignment_lexicon_entries=
#         _SPACE_ = skip, sil
#         _END_ = sil, skip
#         _PUNC_ = sil, skip 
 
        self.processor_name = processor_name
        self.target_nodes = target_nodes
        self.target_attribute = target_attribute
        self.input_label_filetype = input_label_filetype
        self.acoustic_feature_filetype = acoustic_feature_filetype
        self.output_label_filetype = output_label_filetype

        ## Beam search at process time (not training):
        self.viterbi_beam_width_arg = ' '  ## default = no pruning
        if viterbi_beam_width != '':
            self.viterbi_beam_width_arg = ' -t ' + viterbi_beam_width + ' '
    
        self.silence_symbol = silence_symbol
        self.skip_symbol = 'skip'
        self.min_silence_duration = min_silence_duration
        self.silence_tag = silence_tag
        self.n_training_utts = n_training_utts
        self.acoustic_subrecipe = acoustic_subrecipe
        self.training_settings = training_settings      


        self.alignment_lexicon_entries = [(c.POSS_PAUSE, [self.skip_symbol, self.silence_symbol]), (c.PROB_PAUSE, [self.silence_symbol, self.skip_symbol])]

        ## make strings for writing to HTK lexicon file:--
        self.substitutions = []
        self.skippables = [c.POSS_PAUSE, c.PROB_PAUSE] ## this is used by statealigner -- TODO: extend to phone aligner

        ## Is this necessary:- ??
        for (key, values) in self.alignment_lexicon_entries:
            for value in values:
                self.substitutions.append('%s %s'%(key, value))
                if value == self.skip_symbol:
                    if key not in self.skippables:
                        self.skippables.append(key)

        super(SegmentAligner, self).__init__()



    def process_utterance(self, utt):

        if not self.trained:
            sys.exit('Aligner: must be trained before utterances can be processed.')
            
        if not (utt.has_external_data(self.acoustic_feature_filetype) and \
                                        utt.has_external_data(self.input_label_filetype)):
            print "No initial label and/or features for %s"%(utt.get('utterance_name'))
            utt.set("status", "alignment_failed")
            return            
            
        ## Try to align from audio:
        in_lab_dir = utt.get_dirname(self.input_label_filetype) ## dir (not file) for HVite
        out_lab_dir = utt.get_dirname(self.output_label_filetype)## dir (not file) for HVite

        feat_file = utt.get_filename(self.acoustic_feature_filetype) 
        logfile = utt.get_filename("align_log")  ## hardcoded!!!

        """
        ## bypass utts which contain oov words (actually, letters):
        label_seq = readlist(utt.get_filename(self.input_label_filetype))
         for seg in label_seq:
             if seg not in self.model['python_lex']:
                 sys.exit('Can\'t align utterance: segment %s not trained in model'%(seg)) ## 
        """
        
        command = """%s/HVite -l %s -y %s -X %s -C %s -a -m -L %s -T 1 -o S %s -H %s \
                                                        %s %s %s > %s"""%(self.hts_dir,\
                     out_lab_dir, self.output_label_filetype, self.input_label_filetype, \
                    self.model['general.conf'], in_lab_dir, self.viterbi_beam_width_arg, self.model['cmp.mmf'], \
                    self.model['lexicon.txt'], self.model['modellist.mono'], feat_file, \
                     logfile)
        os.system(command)
        
        time_lab = utt.get_filename(self.output_label_filetype)
        if not os.path.isfile(time_lab):
            print "No alignment produced for %s"%(utt.get('utterance_name'))
            utt.set("status", "alignment_failed")
            return
            
        ## If label has been made, merge its info into the utt XML:
        add_segments_from_label(utt, input_label=self.output_label_filetype,\
                                 target_nodes=self.target_nodes, \
                                 target_attribute=self.target_attribute)
                                 
        propagate_start_and_end_times_up_tree(utt) ## to get e.g. token start and end etc.
        
        remove_short_silent_segments(utt, target_attribute=self.target_attribute, \
                                        silence_symbol=self.silence_symbol,  \
                                        min_silence_duration=self.min_silence_duration)
            
        propagate_silence_tag_up_tree(utt, silence_symbol=self.silence_symbol, \
                                        target_attribute=self.target_attribute, \
                                        output_attribute=self.silence_tag)  
         

    def set_is_trained(self):

        ## Try to find aligner components to work out if we are trained:
        self.trained = True
        self.model_dir = os.path.join(self.get_location())
        self.model = {}  ## paths to files containing model components

        for component in ["cmp.mmf", "general.conf", "lexicon.txt", 'modellist.mono']:

            fpath = os.path.join(self.get_location(), component)
            
            if os.path.isfile(fpath):
                self.model[component] = fpath 
            else:
                self.trained = False
            

    def do_training(self, speech_corpus, text_corpus):
        
        self.set_is_trained()

        ## Set path to HTS binaries from voice resources:
        self.hts_dir = self.voice_resources.path[c.BIN]

        ## TODO: fix this -- alignment lexicon entries set in config are not used --
        ##       are hardcoded in scripts/acoustic_model_training/steps/make_alignment_lexicon.sh !!!



        self.extra_substitutions = None        
        if len(self.substitutions) > 0:
            self.extra_substitutions = os.path.join(self.get_location(), 'extra_substitutions.txt')
            writelist(self.substitutions, os.path.join(self.get_location(), 'extra_substitutions.txt'))           

    

        # acoustic features settings, glotthmm only
        self.stream_definitions = ConfigObj(self.get_location()+"/../acoustic_feature_extractor/acoustic_feats.cfg")  ## TODO: fix this! -- share this info in python config and write out when we need it






        ## Double check not trained:
        if self.trained:
            print "Aligner already trained!"
            return

        ## Else proceed to training:
        train_location = os.path.join(self.model_dir, "training")
        print "\n          Training aligner -- see %s/log.txt\n"%(train_location) 
        if not os.path.isdir(train_location):
            os.makedirs(train_location)
      
        feature_dir = os.path.join(self.voice_resources.path[c.TRAIN], \
                                                self.acoustic_feature_filetype)
        label_dir = os.path.join(self.voice_resources.path[c.TRAIN], \
                                                self.input_label_filetype)
        
        ## check labels for successive 'tee' models (breaks HTK):
        #self.check_tee_models(label_dir)
        
        ## Locate training script and default training config:
        script_dir = self.voice_resources.path[c.ACOUSTIC_MODELLING_SCRIPT]
        config_dir = self.voice_resources.path[c.ACOUSTIC_MODELLING_CONFIG]
        training_script = os.path.join(script_dir, self.acoustic_subrecipe+'.sh')
        default_config = os.path.join(config_dir, self.acoustic_subrecipe + '.cfg')


        ## Specialise the default config with settings made in the voice recipe, then
        ## write to bash config file for use by alignment script:
        train_config_fname = os.path.join(train_location, 'train.cfg')
        train_config = ConfigObj(default_config)
        train_config.update(self.training_settings)
        # get stream definitions from feature extractor too
        train_config.update(self.stream_definitions)
        if self.extra_substitutions:
            train_config['EXTRA_SUBSTITUTIONS'] = self.extra_substitutions
        write_bash_config(train_config, train_config_fname)
        
        ## Call the training script:
        command = """%s %s %s %s %s %s | tee %s/log.txt  \
                    | grep 'Aligner training'"""%(training_script, \
                            feature_dir, label_dir, self.hts_dir, train_location, \
                            train_config_fname, train_location)   
        success = os.system(command)
        if success != 0:
            sys.exit('Aligner training failed')
            
        ## Copy the aligner files that need to be preserved:
        assert os.path.isfile(os.path.join(train_location, "final_model", \
                                            "cmp.mmf")),"Aligner training failed"

        for item in ['cmp.mmf', 'config/general.conf','data/lexicon.txt', 'data/modellist.mono']:
            shutil.copy(os.path.join(train_location, 'final_model', item), self.model_dir)
        

        self.set_is_trained()

        #self.load() ## to get new model filenames into self.model's values


### Made redundant by change in scripts/acoustic_model_training/steps/reestimate_alignment_model.sh
#
#    def check_tee_models(self, label_dir, tee_model_words=['_SPACE_', '_PUNC_']):
#        for label in glob.glob(label_dir + '/*.' + self.input_label_filetype):
#            labs = readlist(label)
#            for (i, (first, second)) in enumerate(zip(labs[:-1], labs[1:])):
#                if first in tee_model_words and second in tee_model_words:
#                    sys.exit('Successive tee models in %s, line %s'%(label, i+1))
            


class StateAligner(SegmentAligner):
    '''
    Same as segment aligner, but adds nodes under segments with state timing info.
    Changes to process_utterance function:
        -- added -f to HVite call to get full state alignment
        -- added state_alignment=True to add_segments_from_label 
    '''
    def process_utterance(self, utt):

        if not self.trained:
            sys.exit('StateAligner: must be trained before utterances can be processed.')
            
        if not (utt.has_external_data(self.acoustic_feature_filetype) and \
                                        utt.has_external_data(self.input_label_filetype)):
            print "No initial label and/or features for %s"%(utt.get('utterance_name'))
            utt.set("status", "alignment_failed")
            return            
            
        ## Try to align from audio:
        in_lab_dir = utt.get_dirname(self.input_label_filetype) ## dir (not file) for HVite
        out_lab_dir = utt.get_dirname(self.output_label_filetype)## dir (not file) for HVite

        feat_file = utt.get_filename(self.acoustic_feature_filetype) 
        logfile = utt.get_filename("align_log")  ## hardcoded!!!
        
        command = """%s/HVite -l %s -y %s -X %s -C %s -a -f -m -L %s -T 1 -o S %s -H %s \
                                                        %s %s %s > %s"""%(self.hts_dir,\
                     out_lab_dir, self.output_label_filetype, self.input_label_filetype, \
                    self.model['general.conf'], in_lab_dir, self.viterbi_beam_width_arg, self.model['cmp.mmf'], \
                    self.model['lexicon.txt'], self.model['modellist.mono'], feat_file, \
                     logfile)
        os.system(command)
        
        time_lab = utt.get_filename(self.output_label_filetype)
        if not os.path.isfile(time_lab):
            print "No alignment produced for %s"%(utt.get('utterance_name'))
            utt.set("status", "alignment_failed")
            return
            
        ## If label has been made, merge its info into the utt XML:
        add_segments_and_states_from_label(utt, input_label=self.output_label_filetype,\
                                 target_nodes=self.target_nodes, \
                                 target_attribute=self.target_attribute, \
                                 skippables=self.skippables )  ##TODO: extend this to non-state case
                                 
        propagate_start_and_end_times_up_tree(utt) ## to get e.g. woken start and end etc.
        
#         remove_short_silent_segments(utt, target_attribute=self.target_attribute, \
#                                         silence_symbol=self.silence_symbol,  \
#                                         min_silence_duration=self.min_silence_duration)
#             
        ### didn't work with states!
        remove_short_silent_segments2(utt, target_nodes=self.target_nodes, target_attribute=self.target_attribute, \
                                        silence_symbol=self.silence_symbol,  \
                                        min_silence_duration=self.min_silence_duration)
            


        propagate_silence_tag_up_tree(utt, target_nodes=self.target_nodes, silence_symbol=self.silence_symbol, \
                                        target_attribute=self.target_attribute, \
                                        output_attribute=self.silence_tag)  
         

