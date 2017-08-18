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
        
class VSMTagger(SUtteranceProcessor):

    def __init__(self, processor_name='vsm_tagger', target_nodes='//token', input_attribute='text', \
                    output_attribute_stem='vsm', \
                    norm_counts=True, svd_algorithm='randomized', context_size=250, rank=20, \
                    unseen_method=1, discretisation_method='none', n_discretisation_bins=10, \
                    tokenisation_pattern='(.)', replace_whitespace=False):

        self.processor_name = processor_name
        self.target_nodes = target_nodes
        self.input_attribute = input_attribute
        self.output_attribute_stem = output_attribute_stem
        self.norm_counts = norm_counts
        self.svd_algorithm = svd_algorithm
        self.context_size = context_size
        self.rank = rank
        self.unseen_method = unseen_method
        self.discretisation_method = discretisation_method 
        self.n_discretisation_bins = n_discretisation_bins
        self.tokenisation_pattern = tokenisation_pattern
        self.replace_whitespace = replace_whitespace

        assert self.discretisation_method in ['none', 'uniform', 'standard_set']    
        # standard_set (name from Breiman et al. 1993 section 2.4.1): put boundaries  
        # between each consecutive pair of values

        super(VSMTagger, self).__init__()

        self.parallelisable = False

    def verify(self, voice_resources):
        self.voice_resources = voice_resources
        ## Work out if model is trained already:
        self.table_file = os.path.join(self.get_location(), 'table_file')        
        self.trained = False
        if os.path.isfile(self.table_file + '.table'):
            self.trained = True
    
        ## Load if trained:
        if self.trained:
            if self.discretisation_method == "none":
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

        self.trained = True


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
        
        