#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi


import sys
import os
import re

from util.xpath_extensions_for_ossian import *
## These imports now handled by xpath_extensions_for_ossian:--
#import lxml
#from lxml import etree
#from lxml.etree import * 

import numpy
from naive.naive_util import *   ## now includes helper functions: fix_data_type, final_attribute_name
from util.speech_manip import get_speech, spline_smooth_fzero

import util.acoustic_stats as ac_stats

import default.const as c

#    See  http://lxml.de/1.3/element_classes.html on using custom Element classes:
#      -- can't have an __init__ for UtteranceElement(etree.ElementBase) or any 
#         subclass of etree.ElementBase.

from distutils.spawn import find_executable   # to check if required executables are available





class UtteranceElement(etree.ElementBase):
    """
    Specialised Element class for utterances, has safe_xpath method.
    See here: http://lxml.de/1.3/element_classes.html on using custom Element classes    
    """
    
    def safe_xpath(self, path, default_value='_NA_'):
        """
        Provide padding for e.g. end-of-sentence contexts if xpath doesn't 
        find anything. In order to handle different padding types (e.g. mean vector for 
        VSM features). 
        
        The default padding is _NA_ -- this will be used for e.g. end-of-sentence phone contexts.

        For count based features, xpath gives 0 in sentence-edge positions, which is fine.
        """    
        try:
            if type(path) == XPath:  ## precompiled xpath
                data = path(self)
            else:
                data = self.xpath(path)  ## string representation of xpath
        except lxml.etree.XPathEvalError:           
            sys.exit('Problem evaluating this XPATH: ' + path)
            
        if data == []:
            ## Xpath found nothing, so now try looking for _PADDING for this attribute :
            attribute_name = final_attribute_name(path)           
            #print 'ancestor::utt[1]/attribute::%s_PADDING'%(attribute_name)
            data = self.xpath('ancestor::utt[1]/attribute::%s_PADDING'%(attribute_name))
                     
        if data == []:        
            ## No padding attribute was found, use the default _NA_:
            data = [default_value]
        
        ## Data should be either a float (from count() xpath) or boolean
        assert type(data) in [list, float, bool]
        
        ## or else a list with single entry:
        if type(data) == list:
            assert type(data) == list       
            assert len(data) == 1
            # Take that single entry:
            data = data[0]
            
        ##  convert it to an integer if possible, else
        ## to a string (otherwise class of returned data is: <class
        ## 'lxml.etree._ElementStringResult'>):
        data = fix_data_type(data) 
        return data   
    

    def get_context_vector(self, context_list): 
        """
        Get values for list of contexts at an utterance node.
        
        :param context_list: e.g.: [('name1', 'xpath1'), ('name2', 'xpath2'), ... ]
        :return: vector of features made by concatenating the output of calls to xpath
        on this node. Return list of items like ((name1, value1), (name2, value2), ... )
        """            
        return [(name, self.safe_xpath(path)) for (name, path) in context_list]
        
    def get_context_dict(self, context_list): 
        """
        Get dict of features made by concatenatting the output of calls to xpath
        on this node. Return dict like {feature_name: feature_value, ... }
        """    
        data = dict([(name, self.safe_xpath(path)) for \
                (name, path) in context_list])
        assert len(context_list) == len(data),"Problem with context list: are there duplicate feature names? These should be unique"
        return data

    def has_attribute(self, attribute):
        return (attribute in self.attrib)

    def has_children(self):
        """Does this UtteranceElement have any child nodes?"""
        return  bool(sum([1 for child in self]))

    def pretty_print(self):    
        print tostring(ElementTree(self), pretty_print=True)

    def utterance(self):
        """Get the top-level utterance node of an ``UtteranceElement``."""
        utt = self.xpath("ancestor::utt")
        assert len(utt) == 1  ## node must only have 1 utt
        return utt[0]

    def add_child(self, child_node):
        """Add child to utterance node."""
        self.append(child_node)

    def remove_children(self):
        """Remove any child nodes this UtteranceElement has"""
        for child in self:
            self.remove(child)






# NB: The following lines need to be in this location (i.e. between the definitions of 
# UtteranceElement and Utterance)
#
## See http://lxml.de/1.3/element_classes.html ---
## "If you use a parser at the module level, you can easily redirect a module 
## level Element() factory to the parser method by adding code like this:"
MODULE_PARSER = etree.XMLParser()
lookup = etree.ElementDefaultClassLookup(element=UtteranceElement)
MODULE_PARSER.setElementClassLookup(lookup)
Element = MODULE_PARSER.makeelement



class Utterance(object): 

    """
    -self.data holds xml structure of the utterance.
    
    .. warning:: external data? see add_external_data 
    """

    def __init__(self, string,data_type=None, speech_file=None, utterance_location=None, \
                    speech_location=None, check_single_text_line=True):
        """
        There are 3 modes by which utterances can be initialised: 
            - ``txt`` mode, in which ``string`` argument treated as file containing text of utterance
            - ``utt``mode, in which ``string`` argument treated as file containing existing XML structure of utterance
            - ``str``mode, in which ``string`` argument treated as text of the utterance to be initiliased.
        
        :param string: if ``string`` is the name of an existing file, choose initialisation
             mode ``txt`` or ``utt`` based on its extension. If not a filename, use ``str`` mode.
        :keyword data_type: use this to manually specify mode: must be ``txt``, ``utt`` or ``str``.
        :keyword speech_file: if given, is assumed to point to file containing natural waveform of
                        utterance -- ``waveform`` attribute added to utterance structure. 
        :keyword utterance_location:     **XXX**
        :keyword speech_location:        **XXX**
        :keyword check_single_text_line: **XXX**                                      
        
        
        .. warning:: UPDATE f utt_location is not None, utt filename is assumed to be relative to this, and only partial path is stored in utt structure.

        .. warning:: UPDATE If speech_location is not None, speech_file is assumed to be relative to this, and only partial path is stored in utt structure.
        """

        ## These paths are free to change between sessions -- don't hardcode in config or utt structure:
        self.utterance_location=utterance_location
        self.speech_location=speech_location

        self.acoustic_features = None 

        # First set data_type if none is specified:
        if data_type == None:  	
            try:  ## non-ascii characters in string
                is_a_filename = os.path.isfile(string)
            except:
                is_a_filename  = False
            
            if is_a_filename:
                if string.endswith('.txt'):  
                    data_type = 'txt'
                elif string.endswith('.utt'):
                    data_type = 'utt'    
                else:
                    sys.exit('Unknown file extension for initialising an utterance: %s'%(string[-4:]))
            else:
                data_type = 'str'        
                
        if data_type not in ['str', 'txt', 'utt']:
            sys.exit('Data type %s for initialising utterance is unrecognised'%(data_type))
                                                                                       
        # Now use the data_type to initialise the utterance in the right way:             
        if data_type == 'utt':		        
                
            ## Set the UtteranceElement Element as a default element class
            ## (http://lxml.de/element_classes.html):
            parser_lookup = etree.ElementDefaultClassLookup(element=UtteranceElement)
            ## Ensure pretty printing
            ## (http://lxml.de/FAQ.html#why-doesn-t-the-pretty-print-option-reformat-my-xml-output):
            parser = XMLParser(remove_blank_text=True)
            parser.set_element_class_lookup(parser_lookup)  
            tree = parse(string, parser)
            self.data = tree.getroot()              
#             if "utterance_location" not in dir(self):
            location, name = os.path.split(string)
            self.utterance_location = location
        
            
            if not self.has_attribute("utterance_name"):
                self.data.set("utterance_name", get_basename(string))

        elif data_type == 'txt':
            text = readlist(string)
            """.. todo:: ever really necessary to check single line when init'ing utterance from text?"""
            if check_single_text_line:  
                if len(text) != 1:
                    sys.exit('Cannot initialise an utterance from a text file with mutliple lines: %s'%(''.join(text)))
                string_data = text[0]
            else:
                string_data = ' '.join(text)
                

            self.make_from_string(string_data, speech_file=speech_file)
            try:
                self.data.set("utterance_name", get_basename(string))
            except ValueError:
                print '---'
                print string
                print  get_basename(string)
                print '---'
                sys.exit("Couldn't set utterance name")        

        elif data_type == 'str': 
            self.make_from_string(string, speech_file=speech_file)

        else:
            print 'Data type %s for initialising utterance is unrecognised'%(data_type)

        ## reroute attributes from self.data -> self
        self.attrib = self.data.attrib

    def make_from_string(self, string, speech_file=None):
        """Instantiate an utterance from the a string representing the utterance's text"""
        self.data = Element("utt") ## encoding="utf-8")
        self.data.attrib["text"] = string
        self.data.set("status", "OK") ## OK means use it -- change this if the utt is to be held out
        if speech_file != None:
            self.data.set("waveform", speech_file)
      

    def get_dirname(self, file_type):
        """
        Get the default name for a filetype directory from an utterance's "utterance_filename".
        If utterance_filename is ``<PATH>/utt/name.utt`` the dirname for type
        lab will be ``<PATH>/lab/``. Make the directory if it does not exist already.
        """
        utt_fname = self.get_utterance_filename()
        (utt_dir, fname) = os.path.split(utt_fname)
        (corpus_dir, utt_dir_name) = os.path.split(utt_dir)
        assert  utt_dir_name == "utt"

        dirname = os.path.join(corpus_dir, file_type)
        if not os.path.isdir(dirname):
            os.mkdir(dirname)

        return dirname


    def get_utterance_filename(self):
        """
        Get the absolute path of the utt file where this structure is stored.
        Absolute paths are not stored directly in the structure so that files are portable.
        """
        assert self.utterance_location,"No utterance_location defined for utt -- initialise with utterance_location kw arg"
        assert self.has_attribute("utterance_name")
        return os.path.join(self.utterance_location, self.get("utterance_name")+".utt")    


    def get_filename(self, file_type):
        """
        Get the default name for a filetype from an utterance's ``utterance_filename``.
        If utterance_filename is ``<PATH>/utt/name.utt`` the filename for type
        lab will be ``<PATH>/lab/name.lab``.
        """
        direc = self.get_dirname(file_type)
        base = get_basename(self.get_utterance_filename())
        absolute = os.path.join(direc, base + "." + file_type)
        return absolute

    ###### This (add_external_data) is not in use -- currently filename for new data is got by get_filename.
    ###### The data is not explicitly attached to the utt structure. The existnece of the data can be tested 
    ###### with has_external_data and it is then retrieved with get_filename (again).
##    def add_external_data(self, resource_name, file_name):
##        """
##        Method to add a link to an utterance file resource (e.g. file of MFCCs)
##        by a path relative to the *.utt file.

##        Take (absolute) file_name and convert it to be relative to self.utterance_location
##        to make it less long-winded and more portable. Attach the relative name 
##        to utterance as the value of attribute resource_name.
##        """
##        fullpath = os.path.abspath(os.path.realpath(file_name))
##        relative_path = os.path.relpath(fullpath, self.utterance_location)
##        self.set(resource_name, relative_path)

    def has_external_data(self, resource_name):
        """
        If utt file is ``<PATH>/utt/name.utt`` and resource_name is ``lab``,
        check if ``<PATH>/lab/name.lab`` exists as a file.
        """
        return os.path.isfile(self.get_filename(resource_name))

    def save(self, fname=None):    
        '''
        Save utterance structure as XML to file.
        
        :param fname: write here if specified, otherwise use ``utterance_location``
             if it is set.
        '''
        if not fname:
            if self.utterance_location:
                fname = os.path.join(self.utterance_location, self.get("utterance_name")+".utt")
            else: ## 
                assert self.has_attribute("utterance_filename"),"No file name --- use kwarg"
                fname = self.get("utterance_filename")
        ##print "Write utterance to %s ..."%(fname)
        ElementTree(self.data).write(fname, encoding="utf-8", pretty_print=True)

    def archive(self, fname=None, visualise=True):
        """
        Store an archived version of an utterance that will not be overwritten,
        and also a PDF of a visualisation.
        """    

        if not fname:
            fname = self.get_utterance_filename()

        ## Make a new unique file by appending numbers to filename till we 
        ## have one that does not yet exist:
        i = 0
        while os.path.isfile(fname + "." + str(i).zfill(6) + ".archive"):                
            i += 1
        fname = fname + "." + str(i).zfill(6) + ".archive"
        self.save(fname=fname)    
        self.visualise(fname + ".pdf")

    def pretty_print(self):    
        '''
        [Reroute to self.data]
        '''
        print tostring(ElementTree(self.data), pretty_print=True)


    def all_nodes(self):
        """Get nodes in *document order*"""
        return [el for el in self.data.iterdescendants()] + [self.data]



## reroute some methods of UtteranceElement to work on an utterance's *data*...
## there must be a nicer way of doing this:
    
    
       
    def has_attributes(self):
        """Return list of attribute names stored in utterance.""" 
        return self.data.attrib        

    def has_attribute(self, attribute):
        '''
        [Reroute to self.data]
        '''
        return self.data.has_attribute(attribute)

    def add_child(self, child_node):
        '''
        [Reroute to self.data]
        '''
        self.data.add_child(child_node)

    def xpath(self, path):
        '''
        [Reroute to self.data]
        '''
        #return self.data.xpath(path)
        try:
            data = self.data.xpath(path)
        except lxml.etree.XPathEvalError:
            sys.exit('Problem evaluating this XPATH: ' + path)
        return data
        
    def iterdescendants(self):
        '''
        [Reroute to self.data]
        '''
        return self.data.iterdescendants()

    def append(self, node):
        '''
        [Reroute to self.data]
        '''
        self.data.append(node)

    def insert(self, index, node):
        '''
        [Reroute to self.data]
        '''
        self.data.insert(index, node)

    def remove(self, *args):
        '''
        [Reroute to self.data]
        '''
        self.data.remove(*args)
    
    def get(self, key):
        '''
        [Reroute to self.data]
        Get attribute key's value at *root node* of utterance structure. 
        '''
        return self.data.get(key)
        
    def set(self, key, value):
        '''
        [Reroute to self.data]
        Set attribute key's value at *root node* of utterance structure. 
        '''
        self.data.set(key, value)



    def visualise(self, image_file, force_rows=True, full_label=True, highlight_nodes=None, exclude_tags=[]):
        """
        Use GraphViz to make an image of utterance structure (extension specifies image type).
        
        :keyword force_rows: put nodes with same tag on same vertical level -- true by default
        :keyword full_label: plot all node attributes -- true by default, otherwise, just safetext
        """
        graphviz_data = ['graph "G"{ \n node [style=rounded]']

        node_list = self.all_nodes() ## nodes in document order
        node_list = [node for node in node_list if node.tag not in exclude_tags]

        highlight_ids = []
        if highlight_nodes:
            highlight_ids = [id(node) for node in highlight_nodes]
            print highlight_ids

        ## Node names
        for node in node_list:
            graphviz_data.append("%s ;"%(id(node)))     ## ids will be node name for graphviz.
                                                ## "Declare" these first to ensure good L-R ordering
        ## Node labels
        for node in node_list:
        
            if not full_label:
                if node.get("safetext") == None:
                    label = "%s"%(node.tag)
                else:
                    label = "%s:\\n%s"%(node.tag, node.get("safetext"))
            
            else:
                ## strip characters which will break dot ("):
                bad_characters = ['"']
                data = []
                for (attribute, value) in node.items():
                    for character in bad_characters:
                        value = value.replace(character, '')
                    data.append((attribute, value)) 
                label = ["%s: %s"%(attribute, value) for (attribute, value) in data]   
                label = "\\n".join(label)
                label = node.tag + "\\n" + label
      
            colour_string = ""
            if id(node) in highlight_ids:
                colour_string = ' color="yellow" '

            graphviz_data.append('%s [label="%s" shape="box" %s ] ;'%(id(node), label, colour_string))     
                                               
        
        ## Add arcs:
        for node in node_list:
            if node.getparent() != None:
                parent = node.getparent()
                graphviz_data.append('%s -- %s ;'%(id(parent), id(node)))

        if force_rows: 
            tag_dict = {}
            for node in node_list:
                if node.tag not in tag_dict:
                    tag_dict[node.tag] = []
                tag_dict[node.tag].append(node)    

            for (i, (tag, node_list)) in enumerate(tag_dict.items()):
                ids = [str(id(node)) for node in node_list]
                subgraph = "{ rank=same; "  + " ; ".join(ids)  + "}"
                graphviz_data.append(subgraph)
                                                    
        graphviz_data.append("}")
        
        dotfile = remove_extension(image_file) + ".dot"
        writelist(graphviz_data, dotfile, uni=True)

        image_type = image_file[-3:]
        comm = "dot %s -T%s -o%s"%(dotfile, image_type, image_file)     
        os.system(comm)
        




    def dump_attribute_value_data(self, regex_string):
        """
        Find values for all attributes (matching the supplied regex) from any 
        node of utterance. Do not unique the values (instances not types). 
        
        Return e.g. {"attrib1": ["val1", "val2"], "attrib2": ["val1", "val2", "val3"]}
        """
        dumped = {}
        att_patt = re.compile(regex_string)
        for node in self.all_nodes():
            for attribute in node.keys():
                if re.match(att_patt, attribute):
                    if attribute not in dumped:
                        dumped[attribute] = []
                    dumped[attribute].append(node.get(attribute))                    
        return dumped
    
            
    def dump_features(self, target_nodes, context_list, return_dict=False):
        """
        For each utterance node matching ``target_nodes``, get values for the list of
        contexts at that node.
        """     
        targets = self.xpath(target_nodes)
        #print targets
        
        if len(targets)==0:
#            sys.exit('Pattern %s matches no nodes of utterance %s'%(target_nodes, \
#                                        get_basename(self.get_utterance_filename())))
            print 'Warning: Pattern %s matches no nodes of utterance %s'%(target_nodes, get_basename(self.get_utterance_filename()))
        features = []
        for node in targets:   
            if return_dict: ## keep keys and return as dict
                values = dict(node.get_context_vector(context_list))
            else:  ## remove keys
                values = [value for (name, value) in node.get_context_vector(context_list)]
            features.append(values)
        return features
        
    
    def enrich_with_acoustic_statistics(self, target_nodes, features_dims):
        '''
        Get stats with get_acoustic_statistics for each node in given target_nodes xpath
        and add them to the XML
        '''
        key_string = []
        value_string = []        
        for node in self.xpath(target_nodes):
            for (feature, dim) in features_dims:
                interp = False
                if 'f0' in feature:
                    interp = True
                stats = self.get_acoustic_statistics(node, feature, dim=dim, \
                                        interpolate_fzero=interp)

                for (key,value) in stats.items():
                    key = '%s_%s_%s'%(feature, dim, key)
                    key_string.append(key)
                    value_string.append(str(value))
        key_string = ','.join(key_string)
        value_string = ','.join(value_string)

        node.set('acoustic_stats_names', key_string)
        node.set('acoustic_stats_values', value_string)    
    
    
    def get_acoustic_statistics(self, node, feature, dim=0, acoustic_filetype='cmp', interpolate_fzero=False):
        raw_data = self.get_acoustic_features(node, feature, dim=dim, \
                acoustic_filetype=acoustic_filetype, interpolate_fzero=interpolate_fzero)
        stats = ac_stats.get_stats_over_subsections(raw_data)
        return stats
        
        
    def get_acoustic_features(self, node, feature, dim=0, acoustic_filetype='cmp', interpolate_fzero=False):
        '''
        Get some raw acoustics associated with the given node of the utterance.
        '''
        FRAMESHIFT=5 
        ## get_acoustic_features is likely to be called mutliple times for an utterance,
        ## so store the acoustics in self.acoustic_features on the first call:
        if self.acoustic_features == None:
            #print 'Loading acoustic features....'
            self.load_acoustic_features(acoustic_filetype)
        
        ## work out which dims to gather -- now only allow a single dim to be selected at once
        (from_dim, static_width) = self.acoustic_stream_info[feature]
        if dim > (static_width-1):
            sys.exit('cannot select dim %s from stream %s'%(n_dims, feature))
        selected_dim = from_dim + dim
        
        ## work out which frames to gather:
        from_frame = int(node.get('start')) / FRAMESHIFT
        to_frame = int(node.get('end')) / FRAMESHIFT
        data = self.acoustic_features[from_frame:to_frame, selected_dim]   #  from_dim:to_dim]

        if interpolate_fzero:
#             m,n = numpy.shape(data)
#             assert n==1, 'to interpolate f0, input must be only 1 dimension'
#             data = data[:,0]
            ## trim start of voiced regions, linear interpolate with some smoothing:-
            data = spline_smooth_fzero(data, trim_n_frames=3, s=100, k=1)
#             data = numpy.reshape(data, (m,1))        
        return data


    def add_acoustic_stream_info(self, stream_names, static_stream_sizes):

        assert len(stream_names) == len(static_stream_sizes)
        
        streams = ','.join(stream_names) 
        static_dims = ','.join([str(val) for val in static_stream_sizes])
        
        self.set('acoustic_stream_names', streams)
        self.set('acoustic_stream_dims', static_dims)

    def get_acoustic_stream_info(self):
        '''
        Populate self.acoustic_stream_info and self.acoustic_dim from information 
        stored in XML
        '''
        DELTA = 3 ## assume static + delta + delta-delta
        assert 'acoustic_stream_names' in self.attrib                
        assert 'acoustic_stream_dims' in self.attrib                
        streams = self.get('acoustic_stream_names').split(',')
        static_dims = [int(val) for val in self.get('acoustic_stream_dims').split(',')]
        assert len(streams) == len(static_dims)
        
        self.acoustic_dim = sum(static_dims) * DELTA ## assume delta and delta-delta
        self.acoustic_stream_info = {}
        start = 0
        for (stream, width) in zip(streams, static_dims):
            self.acoustic_stream_info[stream] = (start, width)
            start += width * DELTA

            
    def load_acoustic_features(self, acoustic_filetype):
        #print 'load_acoustic_features'
        self.get_acoustic_stream_info()
        fname = self.get_filename(acoustic_filetype)
        speech = get_speech(fname, self.acoustic_dim , remove_htk_header=True)
        self.acoustic_features = speech
        
    
    def get_waveform_segment(self, node, outfile, padding=0.0):
        '''
        Get the waveform associated with the given node of the utterance.
        '''    
        required_executables = ['sox']
        for executable in required_executables:
            if not find_executable(executable):
                sys.exit('%s command line tool must be on system path '%(executable))
    
            
        if not self.get('waveform'):
            sys.exit('utt has no waveform associated with it')
    
        infile = self.get('waveform')            
        
        ## work out which seconds to extract:
        from_sec = float(node.get('start')) / 1000.0
        to_sec = float(node.get('end')) / 1000.0
        duration = to_sec - from_sec
               
        comm = 'sox %s %s trim %s %s'%(infile, outfile, from_sec-padding, duration+padding)
        #print comm
        os.system(comm)
            
                    
def to_string(utt):
    """.. warning:: USED?"""
    return tostring(utt, pretty_print=True)
    



