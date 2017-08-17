#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

import os
import string
from UtteranceProcessor import SUtteranceProcessor
import default.const as c
from collections import defaultdict
from naive.naive_util import writelist, all_entries_of_type, ms_to_htk, make_htk_wildcards

import numpy
from util.speech_manip import put_speech

## General class for making objects to dump features from utterances (e.g.
## HTS labels, other labels, R format training data for CARTs and others).

## Special names (start_time end_time htk_monophone htk_state) will be handled specially

class FeatureDumper(SUtteranceProcessor):

    def __init__(self, processor_name='feature_dumper', target_nodes='//segment', output_filetype='align_lab', \
                        contexts=[('segment', './attribute::segment_name')], context_separators='commas', \
                        question_file='SomeFileName', question_filter_threshold=0, binary_output=False):

        ## get attributes from config, converting type and supplying defaults:
        self.processor_name = processor_name
        self.target_nodes = target_nodes
        self.context_separators = context_separators
        self.output_filetype = output_filetype
        self.question_file = question_file
        self.question_filter_threshold = question_filter_threshold
        self.contexts = contexts

        self.filter_contexts()

        self.binary_output = binary_output   ## output data flattened, as floats
        if self.binary_output:
            if (self.htk_monophone_xpath or self.htk_state_xpath or self.start_time_xpath or self.end_time_xpath):
                sys.exit('Cannot use features htk_monophone_xpath or htk_state_xpath or start_time_xpath end_time_xpath when dumping to binary format')
            # When dumping data as binary, represent it as space separated values in a string first:--
            self.context_separators = "spaces"


        assert self.contexts != []

        ## TODO: debug this -- when using compiled, doesn't write labels if multiple processors are used (-p 2 etc); check speed increase from compiling...
        '''
        This seems to be the issue mentioned here: http://lxml.de/FAQ.html
        In parallel, things break down silently.
        ##
        "The same applies to the XPath evaluators, which use an internal lock to protect their prepared evaluation contexts. It is therefore best to use separate evaluator instances in threads."
        
        For now, don't use compiled expresssions at all. 
        '''
        if False:
            self.precompile_xpaths()
        
        assert self.context_separators in ["spaces", "commas", "numbers"],"""
                sep '%s' not recognised: must be one of "spaces", "commas", "numbers" """%(self.context_separators)   

        super(FeatureDumper, self).__init__()

        

    def precompile_xpaths(self):
        ## note: type of self.contexts is configobj.Section, not dict, which means that order of 
        ##       self.contexts.items() is well-defined    
        new_contexts = []
        for (name, xpath) in self.contexts:
            compiled_xpath = etree.XPath(xpath)
            new_contexts.append((name, compiled_xpath))
            ## Note that the string representation can be retrieved via path attribute:
            ##  <COMPILEDXPATH>.path
        self.contexts = new_contexts

    def process_utterance(self, utt, make_label=True):

        utt_data = []
        
        utt_questions = defaultdict(int)  ## {}

        nodelist = utt.xpath(self.target_nodes)
        if nodelist == []:            
            print('WARNING: FeatureDumper\'s target_nodes matches no nodes: %s'%(self.config["target_nodes"]))

        for node in nodelist:
            node_data, node_questions = self.get_node_context_label(node)
            utt_data.append(node_data)
            
            ##utt_questions.update(node_questions)
            ## Sum the dictionaries' values:
            for question in node_questions:
                utt_questions[question]+=node_questions[question]

        if make_label:
            label_file = utt.get_filename(self.output_filetype)
            if self.binary_output:
                utt_data = [line.split(' ') for line in utt_data]
                ## In case of string data being present, following line will give:
                ## ValueError: could not convert string to float: a
                utt_data = numpy.array(utt_data, dtype='float')
                put_speech(utt_data, label_file)
            else:
                writelist(utt_data, label_file, uni=True)

        return (utt_data, utt_questions) ## for writing utterance-level labels,
                ## these returned values will be ignored. But these can be used to
                ## acccumulate questions and features over the whole corpus for  
                ## training (see train() method).

    def get_node_context_label(self, node):

        context_vector = node.get_context_vector(self.contexts) 
        ## add numbers:
        context_vector = [(number, name, value) for \
                (number, (name, value)) in enumerate(context_vector)]

        node_questions = defaultdict(int) ## {}
        
        for triplet in context_vector:
            node_questions[triplet] += 1  ## store question's triplet as a key -- sort later  
                                          ## Count can be used for filtering infreq. questions                      

        if self.context_separators=="numbers":
            
            formatted_context_vector = ["%s:%s"%(number, value) 
                    for (number, name, value) in context_vector]       
            formatted_context_vector = "/".join(formatted_context_vector)
            formatted_context_vector = "/" + formatted_context_vector + "/" 
            

        else:
            if self.context_separators=="spaces":
                separator = " "
            elif self.context_separators=="commas":
                separator = ","
            else:
                sys.exit("'%s' not a recognised separator"%(self.context_separators))

            formatted_context_vector = [str(value) for (number, name, value) in context_vector]                   
            formatted_context_vector = separator.join(formatted_context_vector)            

        if self.htk_monophone_xpath:                
            ## PREpend an extra monophone feature -- appending will screw up
            ## extraction of sentence level contexts, which (currently) are
            ## assumed to be at the end of the model name:
            htk_monophone = node.safe_xpath(self.htk_monophone_xpath)
            formatted_context_vector = "-%s+%s"%(htk_monophone, formatted_context_vector)
            ## Don't need to add this to context questions -- just used for 
            ## extracting monophones, not context clustering. 
            ## TODO: find a neater way to handle this? Don't rely on HTK's 
            ## inbuilt monophone extractor in the HTS-Training script?
                               
        if self.htk_state_xpath:                
            ## Increment to start state count at 2 as in HTK
            htk_state = node.safe_xpath(self.htk_state_xpath)
            formatted_context_vector = "%s[%s]"%(formatted_context_vector, htk_state + 1)
                               
        if self.start_time_xpath and self.end_time_xpath:
            start_time = node.safe_xpath(self.start_time_xpath)
            end_time = node.safe_xpath(self.end_time_xpath)

            ## safe_xpath will give _NA_ when times are absent (i.e at runtime) --
            ## in this case, omit times:

            if not (start_time=="_NA_" or end_time=="_NA_"):

                start_time = string.ljust(str(ms_to_htk(start_time)), 10)
                end_time = string.ljust(str(ms_to_htk(end_time)), 10)

                formatted_context_vector = "%s %s %s"%(start_time, end_time, formatted_context_vector)        
        return (formatted_context_vector, node_questions)

    def filter_questions(self, corpus_questions):
        """
        Remove infrequent questions, which cover <  n% or > 100-n% of the training tokens.
        """
        if self.question_filter_threshold > 0:
            filtered = corpus_questions
        else:
            filtered = {}
            for (question, count) in corpus_questions.items():
                if count <= self.question_filter_threshold or count >= 100-self.question_filter_threshold:
                    pass
                else:
                    filtered[question] = count
        return filtered
             
    def format_question_set(self, raw_questions, outfile):
        """
        Take raw_questions: list of (number, name, value) triplets, ...
        
        Write formatted questions to outfile, and human-readable key to outfile.key
        
        Additionally, write question file including continuous questions (CQS) for 
        DNN training
        """

        unique_questions = {}
        for (number, name, value) in raw_questions:
            if (number, name) not in unique_questions:
                unique_questions[(number, name)] = []
            if value not in unique_questions[(number, name)]:
                unique_questions[(number, name)].append(value)
                
        qlist = []        
        cont_qlist = []  ## write continuous questions about numerical features  
        key_list = []  ## To make human-readable key to the feature set
        values_list = []  ## To make reference list of all values taken by a feature  
        
        for ((number, name), values) in sorted(unique_questions.items()):
            values.sort()
            key_list.append((number, name))
            
            
            NA_present = False
            if '_NA_' in values:
                values.remove('_NA_')
                NA_present = True
            
            if all_entries_of_type(values, str):
                ## For strings, make single question for each item, no groups:
                for value in values:
                    qlist.append("QS %s_is_%s {*/%s:%s/*}"%(name, value, number, value))
                    cont_qlist.append("QS %s_is_%s {*/%s:%s/*}"%(name, value, number, value))
                values_list.append((number, name, 'CATEGORICAL', ' '.join(values)))

            elif all_entries_of_type(values, unicode):
                ## For strings, make single question for each item, no groups:
                for value in values:
                    qlist.append("QS %s_is_%s {*/%s:%s/*}"%(name, value, number, value))
                    cont_qlist.append("QS %s_is_%s {*/%s:%s/*}"%(name, value, number, value))
                values_list.append((number, name, 'CATEGORICAL', ' '.join(values)))
                                  
            elif all_entries_of_type(values, int):
                ## For integers, make single question for each item, and also groups 
                ## based on single splits of the range.
                ## Aug 2014: modified -- just use split points -- questions based on 
                ## single values are too arbitrary.
                #
                #for value in values:
                #    qlist.append("QS %s_is_%s {*/%s:%s/*}"%(name, value, number, value))
                
                values_list.append((number, name, 'NUMERIC', 'MAX:'+str(max(values))))
                
                cont_qlist.append("CQS %s {*/%s:(\d+)/*}"%(name, number))
                
                qlist.extend([""]) ## for formatting of final file    
                for split_point_ix in range(1, len(values)):

                    split_point = values[split_point_ix]
                    
                    wildcard_values = make_htk_wildcards(split_point)
                    formatted_sublist = ["/%s:%s/"%(number, value) for value in wildcard_values]
                    formatted_sublist = "*,*".join(formatted_sublist)
                    
                    qlist.append("QS %s_<_%s {*%s*}"%(name, split_point, formatted_sublist)) 

            elif all_entries_of_type(values, float):
                ## floats -- only make CQS
                
                values_list.append((number, name, 'NUMERIC', 'MAX:'+str(max(values))))
                
                ## NB_  special regex to handle decimal point! --
                cont_qlist.append("CQS %s {*/%s:([\d\.]+)/*}"%(name, number))
                

            
            else:
                print "Feature values of mixed type / not string or int:"
                print values
                sys.exit(1)
    
                    
            if NA_present:        
                qlist.append("QS %s_is__NA_ {*/%s:_NA_/*}"%(name, number))
                cont_qlist.append("QS %s_is__NA_ {*/%s:_NA_/*}"%(name, number))
            
            qlist.extend(["", "", ""]) ## for formatting of final file
            cont_qlist.extend(["", "", ""]) ## for formatting of final file
            

                        
        writelist(qlist, outfile, uni=True)    
        writelist(cont_qlist, outfile + '.cont', uni=True)

        key_list = ["/%s:\t%s"%(number, name) for (number, name) in key_list]
        key_file = outfile + ".key"
        writelist(key_list, key_file, uni=True)    
        
        
        values_list = ["%s\t%s\t%s\t%s"%(number, name, feat_type, values) \
                        for (number, name, feat_type, values) in values_list]
        values_file = outfile + ".values"
        writelist(values_list, values_file, uni=True)    
        
        
#     def parse_context_list(self):
#         """
#         Use string-list (not section) in config to preserve order if input as dictionary.
#         """
# 
#         self.context_list = []
#         for line in self.config['context_list']:
#             split_line = re.split("\s+", line)
#             assert len(split_line) == 2,"Context list must contain 1 name and 1 xpath experission per line -- bad line: %s"%(line)
#             self.context_list.append(split_line)
# 
#     def filter_context_list(self):
#         """
#         Handle special names : start_time end_time htk_monophone
#         """
#         self.start_time_xpath = None
#         self.end_time_xpath = None
#         self.htk_monophone_xpath = None    
# 
#         filtered_context_list = []
#         for (name, xpath) in self.context_list:
#             
#             if name=="start_time":
#                 self.start_time_xpath = xpath
#             elif  name=="end_time":
#                 self.end_time_xpath = xpath
#             elif name=="htk_monophone":
#                 self.htk_monophone_xpath = xpath
#             else:
#                 filtered_context_list.append([name, xpath])
#         self.context_list = filtered_context_list


    def filter_contexts(self):
        """
        Handle special names : start_time end_time htk_monophone htk_state
        """
        self.start_time_xpath = None 
        self.end_time_xpath = None
        self.htk_monophone_xpath = None    
        self.htk_state_xpath = None

        filtered_contexts= []
        
        for line in self.contexts:
            #print line
            (name, pattern) = line
            if name == 'start_time':
                self.start_time_xpath = pattern
            elif name == 'end_time':
                self.end_time_xpath = pattern
            elif name == 'start_time':
                self.start_time_xpath = pattern
            elif name == 'htk_monophone':
                self.htk_monophone_xpath = pattern
            elif name == 'htk_state':
                self.htk_state_xpath = pattern
            else:
                filtered_contexts.append((name, pattern))                                    
        self.contexts = filtered_contexts
                                    
                                    
        
        
    def get_corpus_header(self):

        header = [name for (name, xpath) in self.context_list]
        if self.context_separators=="spaces":
            separator = " "
        elif self.context_separators=="commas":
            separator = ","
        else:
            sys.exit("'%s' not a recognised separator for dumping corpus"%(self.context_separators))
        header = separator.join(header)
        return header


    def do_training(self, speech_corpus, text_corpus):
        """
        'Training' a feature dumper means writing a question file 
        [previously also  aggregated corpus feature file from all utts in the corpus,
        but this is skipped now]
        """
        
        self.question_file_path = self.voice_resources.get_filename(self.question_file, c.TRAIN)

        if os.path.isfile(self.question_file_path):  
            print 'FeatureDumper already trained -- questions exist:'
            print self.question_file_path
            return
     
        corpus_questions = defaultdict(int) ## {} ## store questions as keys to unique them

        
        for utt in speech_corpus:            
           
            (utt_data, utt_questions) = self.process_utterance(utt, make_label=False)
            ## sum question counts:
            for question in utt_questions:
                corpus_questions[question]+=utt_questions[question]
              
            ##corpus_questions.update(utt_questions)
       
        corpus_questions = self.filter_questions(corpus_questions)
            
        
           
        self.format_question_set(corpus_questions.keys(), self.question_file_path)
                                 


class FeatureDumperWithSubstates(FeatureDumper):
    '''
    This is only for efficiency -- xpath evaluations are expensive.
    When FeatureDumper iterates over states, most of the work (at phone level and above)
    is repeated 5 times.  
    '''
    def load(self):
        super(FeatureDumperWithSubstates, self).load()
        
        self.state_tag = self.config.get('state_tag', 'state')
        self.start_attribute = self.config.get('start_attribute', 'start')
        self.end_attribute = self.config.get('end_attribute', 'end')
                        
                        
    def process_utterance(self, utt, make_label=True):

        utt_data = []        
        utt_questions = defaultdict(int) 

        nodelist = utt.xpath(self.config["target_nodes"])
        if nodelist == []:            
            print('WARNING: FeatureDumper\'s target_nodes matches no nodes: %s'%(self.config["target_nodes"]))

        for node in nodelist:
            
            self.htk_state_xpath = None ## make sure this is none.
            self.start_time_xpath = None
            self.end_time_xpath = None

                
            ## for phone!:--          
            node_data, node_questions = self.get_node_context_label(node)
            
            statelist = node.xpath('.//'+self.state_tag)
            assert statelist != []
            for (i, state) in enumerate(statelist):
            
                state_ix = i + 2
                state_node_data = "%s[%s]"%(node_data, state_ix)
            
                
                start_time = state.attrib.get(self.start_attribute, '_NA_')  ## no time at runtime!
                end_time = state.attrib.get(self.end_attribute, '_NA_')

                if not (start_time=="_NA_" or end_time=="_NA_"):

                    start_time = string.ljust(str(ms_to_htk(start_time)), 10)
                    end_time = string.ljust(str(ms_to_htk(end_time)), 10)

                    state_node_data = "%s %s %s"%(start_time, end_time, state_node_data)     
                
                utt_data.append(state_node_data)
                
            ##utt_questions.update(node_questions)
            ## Sum the dictionaries' values:
            for question in node_questions:
                utt_questions[question]+=node_questions[question]
                       
        if make_label:
            label_file = utt.get_filename(self.config["output_filetype"])
            writelist(utt_data, label_file, uni=True)


        return (utt_data, utt_questions) ## for writing utterance-level labels,
                ## these returned values will be ignored. But these can be used to
                ## acccumulate questions and features over the whole corpus for  
                ## training (see train() method).    



class MappedFeatureDumper(FeatureDumper):

    '''
    Allow features to be mapped to vector representations (sparse or dense) using mapper based on e.g. phone table or VSM.
    All output features are assumed to be numerical; a trivial question file (consisting of all CQS) is written to keep Merlin happy.
    TODO: assert all features *are* numerical on extraction.
    '''

    def __init__(self, **kwargs):

        super(MappedFeatureDumper, self).__init__(**kwargs)

        ## separate contexts and mappers:--
        self.mappers = {}
        contexts_without_mappers = []
        for (i,context) in enumerate(self.contexts):
            if len(context) == 3:
                contexts_without_mappers.append(context[:2])
                self.mappers[i] = context[2]
            else:
                assert len(context) == 2
                contexts_without_mappers.append(context)
        self.contexts = contexts_without_mappers

        ## make list of names with all features mapped:
        self.mapped_feature_names = []
        for (i, (name, xpath)) in enumerate(self.contexts):
            if i in self.mappers:
                mapped_names = [name + ':' + field_name for field_name in self.mappers[i].feature_names]
                self.mapped_feature_names.extend(mapped_names)
            else:
                self.mapped_feature_names.append(name)

        self.number_of_features = len(self.mapped_feature_names)

    def process_utterance(self, utt):
        #print('!!! in MappedFeatureDumper::process_utterance')
        utt_data = []
        
        nodelist = utt.xpath(self.target_nodes)
        if nodelist == []:            
            print('WARNING: FeatureDumper\'s target_nodes matches no nodes: %s'%(self.config["target_nodes"]))

        for node in nodelist:
            node_data = self.get_node_context_label(node)
            utt_data.append(node_data)

        label_file = utt.get_filename(self.output_filetype)
        writelist(utt_data, label_file, uni=True)



    def do_training(self, speech_corpus, text_corpus):
        """
        'Training' a feature dumper means writing a question file 
        In the case of mapped feature dumper, all features are assumed to be numerical, so this is trivial
        """
        self.question_file_path = self.voice_resources.get_filename(self.question_file, c.TRAIN)

        if os.path.isfile(self.question_file_path):  
            print 'FeatureDumper already trained -- questions exist:'
            print self.question_file_path
            return
       
        self.make_simple_continuous_questions(self.question_file_path)
                                 
    def make_simple_continuous_questions(self, outfile):
     
        cont_qlist = []  ## write continuous questions about numerical features  
        key_list = []
        
        for (number, name) in enumerate(self.mapped_feature_names):
                
            ## NB_  special regex to handle decimal point! --
            cont_qlist.append("CQS %s {*/%s:([\d\.]+)/*}"%(name, number))
            key_list.append("/%s:\t%s"%(number, name))

        writelist(cont_qlist, outfile + '.cont', uni=True)

        key_file = outfile + ".key"
        writelist(key_list, key_file, uni=True)    
        
        
    def get_node_context_label(self, node):

        #print('in MFD get_node_context_label')
        context_vector = node.get_context_vector(self.contexts) 

        mapped_context_vector = []
        for (i, (name, value)) in enumerate(context_vector):
            if i in self.mappers:
                #mapped_names = [name + '=' + field_name for field_name in self.mappers[i].feature_names]
                mapped_values = self.mappers[i].lookup(value)
                # mapped_context_vector.extend(zip(mapped_names, mapped_values))
                mapped_context_vector.extend(mapped_values)
            else:
                mapped_context_vector.append(value)

 
        ## add numbers:
        assert len(mapped_context_vector) == self.number_of_features

        context_vector = zip(range(self.number_of_features), self.mapped_feature_names, mapped_context_vector)

    
        # At this point, context_vector looks like this:
        #
        # [(0, u'll_segment:cmanner=affric', 0.0), (1, u'll_segment:cmanner=approx', 0.0), (2, u'll_segment:cmanner=fric', 0.0), (3, u'll_segment:cmanner=lateral', 0.0), (4, u'll_segment:cmanner=nasal', 1.0), (5, u'll_segment:cmanner=stop', 0.0), (6, u'll_segment:cplace=alveolar', 0.0),
        if self.context_separators=="numbers":
            
            formatted_context_vector = ["%s:%s"%(number, value) 
                    for (number, name, value) in context_vector]       
            formatted_context_vector = "/".join(formatted_context_vector)
            formatted_context_vector = "/" + formatted_context_vector + "/" 
            

        else:
            if self.context_separators=="spaces":
                separator = " "
            elif self.context_separators=="commas":
                separator = ","
            else:
                sys.exit("'%s' not a recognised separator"%(self.context_separators))

            formatted_context_vector = [str(value) for (number, name, value) in context_vector]                   
            formatted_context_vector = separator.join(formatted_context_vector)            

        if self.htk_monophone_xpath:                
            ## PREpend an extra monophone feature -- appending will screw up
            ## extraction of sentence level contexts, which (currently) are
            ## assumed to be at the end of the model name:
            htk_monophone = node.safe_xpath(self.htk_monophone_xpath)
            formatted_context_vector = "-%s+%s"%(htk_monophone, formatted_context_vector)
            ## Don't need to add this to context questions -- just used for 
            ## extracting monophones, not context clustering. 
            ## TODO: find a neater way to handle this? Don't rely on HTK's 
            ## inbuilt monophone extractor in the HTS-Training script?
                               
        if self.htk_state_xpath:                
            ## Increment to start state count at 2 as in HTK
            htk_state = node.safe_xpath(self.htk_state_xpath)
            formatted_context_vector = "%s[%s]"%(formatted_context_vector, htk_state + 1)
                               
        if self.start_time_xpath and self.end_time_xpath:
            start_time = node.safe_xpath(self.start_time_xpath)
            end_time = node.safe_xpath(self.end_time_xpath)

            ## safe_xpath will give _NA_ when times are absent (i.e at runtime) --
            ## in this case, omit times:

            if not (start_time=="_NA_" or end_time=="_NA_"):

                start_time = string.ljust(str(ms_to_htk(start_time)), 10)
                end_time = string.ljust(str(ms_to_htk(end_time)), 10)

                formatted_context_vector = "%s %s %s"%(start_time, end_time, formatted_context_vector)        
        return formatted_context_vector


    def filter_contexts(self):
        """
        Handle special names : start_time end_time htk_monophone htk_state
        """
        self.start_time_xpath = None 
        self.end_time_xpath = None
        self.htk_monophone_xpath = None    
        self.htk_state_xpath = None

        filtered_contexts= []
        
        for line in self.contexts:
            use_mapper = False
            if len(line) == 3:
                use_mapper = True
                (name, pattern, mapper) = line
            elif len(line) == 2:
                (name, pattern) = line
            else:
                sys.exit('context must either be of form (name, pattern) or (name, pattern, mapper)')
            if name == 'start_time':
                self.start_time_xpath = pattern
            elif name == 'end_time':
                self.end_time_xpath = pattern
            elif name == 'start_time':
                self.start_time_xpath = pattern
            elif name == 'htk_monophone':
                self.htk_monophone_xpath = pattern
            elif name == 'htk_state':
                self.htk_state_xpath = pattern
            else:
                if use_mapper:
                    filtered_contexts.append((name, pattern, mapper))                                    
                else:
                    filtered_contexts.append((name, pattern))                                    

        self.contexts = filtered_contexts
                                    
          