#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

from UtteranceProcessor import *
from util.NodeProcessors import *
from util.discretise_vsm import *
from util.LookupTable import *

try:
    import regex as new_regex
except ImportError:
    sys.exit('Please install "regex": https://pypi.python.org/pypi/regex ')
    
import codecs
from naive.naive_util import readlist
from naive.naive_util import readlist as naive_readlist

from naive.train_static_vsm import train_static_vsm
        
class VSMTagger(UtteranceProcessor):

    def load(self):  
        
        ## Attributes from config (with defaults):
        self.target_nodes = self.config.get('target_nodes', '//token')
        self.input_attribute = self.config.get('input_attribute', 'text')
        self.output_attribute_stem = self.config.get('output_attribute_stem', 'vsm')
        
        self.use_ntokens = int(self.config.get('use_ntokens', 0)) ## no longer used
        
        ## 2 new options:
        self.norm_counts = self.config.get('norm_counts', True)
        self.svd_algorithm = self.config.get('svd_algorithm', 'randomized')
        
        self.context_size = int(self.config.get('context_size', 250))
        self.rank = int(self.config.get('rank', 20))
        self.unseen_method = int(self.config.get('unseen_method', 1))
        self.discretisation_method = self.config.get('discretisation_method', 'none')   ## "standard_set"
        self.n_discretisation_bins = int(self.config.get('n_discretisation_bins', 10))

        self.tokenisation_pattern = self.config.get('tokenisation_pattern', '(.)')
        self.replace_whitespace = self.config.get('replace_whitespace', False)

        assert self.discretisation_method in ['none', 'uniform', 'standard_set']    
            # standard_set -- (name from Breiman et al. 1993 section 2.4.1) put boundaries  
            # between each consecutive pair of values


        ## Work out if model is trained already:
        self.table_file = os.path.join(self.get_location(), 'table_file')        
        self.trained = False
        if os.path.isfile(self.table_file + '.table'):
            self.trained = True
    
        ## Load if trained:
        if self.trained:
            if self.config["discretisation_method"] == "none":
                self.vsm = LookupTable(self.table_file + ".table")
            else:
                self.vsm = LookupTable(self.table_file + ".table.disc")


    def process_utterance(self, utt):        

        for i in range(1, self.rank + 1):
            enrich_nodes( utt, function=self.vsm.lookup,
                          target_nodes=self.target_nodes, 
                          input_attribute=self.input_attribute,
                          output_attribute="%s_d%s"%(self.output_attribute_stem, i), 
                          kwargs={"field": "dim_%s"%(i)}) 

            ## Add padding values for VSM:    
            padding_name = "%s_d%s_PADDING"%(self.output_attribute_stem, i)        
            padding_value = self.vsm.get_padding_value(field="dim_%s"%(i))    
            utt.set(padding_name, padding_value)


    def do_training(self, speech_corpus, text_corpus):
        ## Double check not trained:
        if self.trained:
            print 'VSM tagger already trained'
            return
        
        ## Write training text to a single file:
        train_dir = os.path.join(self.get_location(), 'training')
        if not os.path.isdir(train_dir):
            os.mkdir(train_dir)
        train_file = os.path.join(train_dir, 'train_data.txt')
        
        f = codecs.open(train_file, 'w', encoding='utf-8')
        for utterance in speech_corpus:
            text = utterance.get('text')
            text = self._process_text_line(text)
            f.write(text + '\n')
        
        ## Now add lines from optional long extra file(s):
        for fname in text_corpus:
            for line in naive_readlist(fname):
                text = self._process_text_line(line)
                f.write(text + '\n')
        
        f.close()
                

        ## Train VSM -- use new streamlined train_static_vsm script:
        assert self.unseen_method >= 1,'Unseen method must be >= 1'
        train_static_vsm(train_file, self.table_file, self.context_size, self.rank, \
                            self.unseen_method, self.svd_algorithm, self.norm_counts)

        
        ## discretise the features in the VSM tables before putting into voice:
        self.table_file += ".table"  ## train_static_vsm uses common stem for several 
                                     ## outputs -- tidy this up?
        
        if  self.discretisation_method == "none":
            self.vsm = LookupTable(self.table_file)

        else:
            disc_table_file = self.table_file + ".disc"
            method = self.discretisation_method # "standard_set"
            nbins = self.n_discretisation_bins
            discretise_vsm(self.table_file, disc_table_file, method, nbins)

            ## make the resulting (discretised) VSM table into LookupTable objects:
            self.vsm = LookupTable(disc_table_file)       

        self.config["is_trained"] = True


    def _process_text_line(self, text):            

        split_text = [token for token in new_regex.split(self.tokenisation_pattern, text) \
                            if token != '']
        if self.replace_whitespace:
            new_text = []
            for token in split_text:
                if token.isspace():
                    new_text.append(self.replace_whitespace)                        
                else:
                    new_text.append(token)  
            split_text = new_text
        
        split_text = [token.strip(u' ') for token in split_text]  ## prevent multiple spaces
        split_text = [token for token in split_text if token != u'']  ## prevent multiple spaces
        split_text = [token.lower() for token in split_text]     ## lowercase
        text = ' '.join(split_text) 
        return text
        
        