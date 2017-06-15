#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi


import codecs
import unicodedata
import re
import sys
import string
import os
from operator import itemgetter
sys.path.append(".")
from configobj import ConfigObj
import inspect
import struct

from lxml.etree import XPath

utterance_end_token = "_UTTEND_"   ## where to put global constants like this?

##-------- unicode handling --------

def safetext(unicode_string):
    unicode_string = unicode(unicode_string)
    safetext = ''
    for char in unicode_string:
        safetext += unicode_character_to_safetext(char)    
    return safetext
    
def unicode_character_to_safetext(char):
    '''
    work one out. The substitute 
    should be safe to use with applications of interest (e.g. in HTK modelnames), and
    a perhaps over-cautious subset of ASCII is used for this (uppercase A-Z).
    
    TODO: [make this explanation complete]
    
     To enable 
    reverse mapping, multicharacter safetexts are delimited with _. 
    '''
    ## Replacements to make greedily within unicode name:
    name_reps = {" ": "",
                 "-": "",
                 "0": "ZERO",
                 "1": "ONE",
                 "2": "TWO",
                 "3": "THREE",
                 "4": "FOUR",
                 "5": "FIVE",
                 "6": "SIX",
                 "7": "SEVEN",
                 "8": "EIGHT",
                 "9": "NINE"     }
    if char in list("abcdefghijklmnopqrstuvwxyz"):
        substitute = char
    else:          
        try:
            substitute = unicodedata.name(char)
        except ValueError:   ## got ValueError: no such name
            substitute = "PROBLEM_CHARACTER"
        for key in name_reps.keys():
            substitute = substitute.replace(key, name_reps[key])
        substitute = "_" + substitute + "_"    
    return substitute



##-------- config processing -------
def config_list(value):
    '''
    ConfigObj handles reading of string lists without validation, but in the case of 
    1-item lists, strings will of course be returned. This function does type checking
    and conversion for this case.
    '''
    if isinstance(value, list):
        return value
    else:
        return [ value ]


def reformat_ini_to_htk(infile, outfile):
    config = ConfigObj(infile, encoding='UTF8', interpolation="Template")
    config = ['%s = %s'%(key,value) for (key,value) in config]
    config = '\n'.join(config) + '\n'
    writelist(config, outfile, uni=True)

##-----------------------------------

def read_lettermap(fname, uni=True):
    data = readlist(fname, uni=uni)
    data = [line.strip(" \t") for line in data]
    data = [item for item in data if item != ""]    
    data = [re.split("\s+", line) for line in data]
    
    for pair in data:
        assert len(pair)==2,"%s doesn't have 2 elements"%(pair)
    data = dict(data)
    return data


def in_unicode_table(unicode_string):
    try:
        test = [unicodedata.name(character) for character in unicode_string]       
        return 1            
    except ValueError:
        return 0
        
def readlist(filename, uni=True, check_unicode_database=False):
    if uni:
        f = codecs.open(filename, encoding='utf-8')
    else:    
        f = open(filename, "r")
    data = f.readlines()
    f.close()
    data = [line.strip("\n\r") for line in data]
    if check_unicode_database:
        test = [in_unicode_table(line) for line in data]
        data = [line for (line, value) in zip(data, test) if value==1]
        if len(test)-sum(test) > 0:
            print "Skipped %s lines of %s because couldn't find a character in unicode database"%(len(test)-sum(test), filename)
    return data


    
def writelist(data, filename, uni=False):
    '''
    The default for writing utf-8 is False. This is important because the default should
    be to write ascii compatible files (for compatibility with HTK etc.)
    '''

    if uni:
        data=[unicode(x) for x in data]
        f = codecs.open(filename, 'w', encoding='utf-8')
    else:
        data=[str(x) for x in data]
        f = open(filename, "w")    
    data = "\n".join(data)  +  "\n"
    f.write(data)
    f.close()
    
    
def remove_extension(fname):
    """Remove everything in a string after the last dot, and the dot itself"""
    return re.sub("\.[^\.]+\Z", "", fname)    

def find_extension(fname):
    """Return everything in a string after the last dot"""    
    return fname.split(".")[-1]

    
def get_basename(fname):
    """Remove path and extenstion"""
    return remove_extension(os.path.split(fname)[-1])

def burst_safestring(string):
    ## TODO: rename safetext?!
    return re.findall("(_[^_]+_|[^_])", string)    
def burst_safestring_to_string(string):
    ## TODO: rename safetext?!
    return " ".join(burst_safestring(string))


def section_to_config(section):
    """
    Take a section from a ConfigObj and make it into new ConfigObj
    """
    new_conf = ConfigObj()
    for (key, value) in section.items():
        new_conf[key] = value
    return new_conf

"""    
def read_xwaves_label(fname):
    label = readlist(fname)
    keep = []
    header = True
    for line in label:
        if not header:
            keep.append(line)
        if line == "#":
            header = False
"""


def read_htk_label(fname):
    """
    Read HTK label, assume: "start end phone word", where word is optional.
    Convert times from HTK units to MS
    """
    label = readlist(fname)
    label = [re.split("\s+", line) for line in label] ## split lines on whitespace
    parsed_label = []
    
    for line in label:
        if len(line)==3:
            (start,end,segment) = line
            word = ""
        elif len(line)==4:
            (start,end,segment,word) = line
        else:
            print "Bad line length:"
            print line
            sys.exit(1)    
        end = htk_to_ms(int(end))
        start = htk_to_ms(int(start))                
        parsed_label.append([int(start), int(end), segment, word])
    return parsed_label

def read_htk_state_label(fname):
    """
    Read HTK label with state alignment
    
    return [word, [seg, [s1, start, end], [s2, start , end] ... ]]]
    """
    label = readlist(fname)
    label = [re.split("\s+", line) for line in label] ## split lines on whitespace
    
    parsed = []
    
    word = []
    for line in label:
        
        assert len(line) in [3,5],"Bad line length: %s"%(line)
        if len(line)==3:
            word.append(line)
        elif len(line)==5:
            if word != []:
                parsed.append(word)
            word = [line[3], line[4], line[:3]]
    parsed.append(word)
    
    ## convert times -> ms
    converted = []
    for line in parsed:
        converted_line = [line[0], line[1]]
        for entry in line[2:]:
            (start,end,state) = entry
            converted_line.append([int(htk_to_ms(int(start))) , int(htk_to_ms(int(end))) , state])
        converted.append(converted_line)
    return converted
        

def fix_initial_and_final_times(label, initial_increment, final_increment, framesize=5):

    initial_increment_ms = initial_increment * framesize
    final_increment_ms = final_increment * framesize

    converted = []
    for (line_num, line) in enumerate(label):
        converted_line = [line[0], line[1]]
        for (i,entry) in enumerate(line[2:]):
            (start,end,state) = entry
            
            if line_num==0 and i == 0: ## first state of first segment
                start = start
                end = end + final_increment_ms
            elif line_num+1 == len(label) and i+1 == len(line[2:]): ## last state in last segment
                start = start + initial_increment_ms
                end = end + initial_increment_ms + final_increment_ms
            else:
                start = start + initial_increment_ms
                end = end + initial_increment_ms
                
            converted_line.append([start , end , state])
        converted.append(converted_line)
    return converted
    
    
def htk_to_ms(htk_time):
    """
    Convert time in HTK (100 ns) units to ms
    """
    if type(htk_time)==type("string"):
        htk_time = float(htk_time)
    return htk_time / 10000.0

def ms_to_htk(ms_time):
    """
    Convert time in ms to HTK (100 ns) units 
    """
    if type(ms_time)==type("string"):
        ms_time = float(ms_time)    
    return int(ms_time * 10000.0)

def all_entries_of_type(sequence, test_type):
    """
    If all elements of sequence are of type test_type, return True, else False.
    """
    return sum([int(type(x)==test_type) for x in sequence]) == len(sequence)
                
def int_to_alphabetic(number): 
    """Convert non-negative integer to base 26 representation using uppercase A-Z
    as symbols. Can use this instead of numbers in feature delimiters because:
        -- gives shorter full context model names (esp. with many features)
        -- trivially, split-context-balanced.py expects delimiters to contain no digits        
    """    
    assert number >= 0,"Function not intended to handle negative input values"    
    if number == 0:
        return string.uppercase[0]    
    alphabetic = ""
    current = number
    while current!=0:
        remainder = current % 26
        remainder_string = string.uppercase[remainder]        
        alphabetic = remainder_string + alphabetic
        current = current / 26
    return alphabetic


def read_feature_lexicon(input_fname, dims_to_keep=0):
    """
    Assumed format:   lemma feature1 feature2 feature3 ...      per line    
    Features are numeric.
    
    default dims_to_keep = 0 means keep all
    """
    print "reading " + input_fname + " ..."
    lex={}
    data = readlist(input_fname)

    data = [re.split("\s+", line) for line in data]
    
    if dims_to_keep > 0:
        data = [line[:dims_to_keep+1] for line in data]  ## +1: include lemma
    
    line_length = len(data[0]) ## first line length
        
    for line in data:
        assert len(line) == line_length
        lex[line[0]] = [float(item) for item in line[1:]]
        
    nfeat = line_length - 1 ## account for lemma
    return lex, nfeat          


def unique_append(old_list, new_list):
    """
    Add items from new_list to end of old_list if those items are not 
    already in old list -- returned list will have unique entries. 
    Preserve order (which is why we can't do this quicker with dicts).
    """
    combined = old_list
    for item in new_list:
        if item not in combined:
            combined.append(item)
    return combined            



          
        
def read_table(fname, n_entries=2):
    """
    Function for reading config files, context files etc.
    Strip comments (#) and empty lines.
    """ 
    assert os.path.isfile(fname)
    data = readlist(fname)                  
    data = [line.strip("\n ") for line in data]
    
    comment_patt = re.compile("\s*#.*")
    data = [re.sub(comment_patt, "", line) for line in data] ## strip comments
    
    data = [line for line in data if line != ""]
    data = [re.split("\s+", line) for line in data]
    
    #print data
    
    ## check correct number of items per line:
    assert sum([len(line) for line in data]) == (n_entries * len(data)) ## 

    return data 


def write_r_datafile(data, fname):
    """
    Take data, in the form of a list of lists like:
    :
        [(0, u'response', 'True'), (1, u'token_text', '_COMMA_') [...]
        
    I.e. feature number, feature name, feature value for each
    feature on a line. Feature names must be same on each line.
    Write data file for R where first line is header with feature names,
    and each line contains feature values for one data point.
    """ 
    header = [key for (number, key, value) in data[0]]
    table = []
    
    for line in data:
        keys = [key for (number, key, value) in line]
        assert keys == header
        values = [value for (number, key, value) in line]
        table.append(values)
    
    outdata = [header] + table

    outdata = [[str(item) for item in line] for line in outdata] # ensure all strings

    outdata = [','.join(line) for line in outdata]
    writelist(outdata, fname)



def flatten_mapping(mapping, sort_by=False, reverse_sort=False):       
    '''
    Turn dict of dicts to list of (key, value) pairs (with unicode keys and values).
     Each subdict must contain the same keys -
    these (together with lemma_name) will make up header entries.

    TODO: assert tab character not inside keys / values

    '''
    ## Check data -- does each point have same fields?:
    fields = sorted(mapping.values()[0].keys()) ## pick one item's keys to compare against
    for (key, subdict) in mapping.items():
        assert sorted(subdict.keys()) == fields

    header = ["HEADER"] + fields

    data = []
    lemmas = mapping.keys()
    for lemma in lemmas:
        line = [lemma] + [mapping[lemma][var] for var in fields]
        data.append(line)

    sort_indexes = []
    if sort_by:
        assert type(sort_by) == list,"sort_by must be a list of field names to sort by (in order)"
        for value in sort_by:
            sort_indexes.append(header.index(value))            
    sort_indexes.append(0)

    data = [header] + sorted(data, key=itemgetter(*sort_indexes), reverse=reverse_sort)

    ## freq.s are ints -- handle this:
    newdata = []
    for line in data:
        #print [line]
        newline = []
        for item in line:
            if type(item) == unicode:
                newline.append(item)
            else:
                newline.append(unicode(item)) 
        newdata.append(newline)
    data = newdata

    for line in data:
        for item in line:
            assert unicode("\t") not in item

    data = [(line[0], "\t".join(line[1:])) for line in data]

    return data



def unflatten_mapping(mapping):       
    '''
    Reverse flatten_mapping. Take dict-like object (e.g. config section), assume utf-8 coded
    '''
    ## decode utf-8 bytestrings to unicode strings:
    mapping = dict([(key.decode("utf-8"), val.decode("utf-8")) for (key,val) in mapping.items() ])

    ## split values on tab character:
    split_dict = {}
    for key in mapping.keys():
        split_dict[key] = mapping[key].split("\t")

    assert "HEADER" in split_dict
    header = split_dict["HEADER"]
    del split_dict["HEADER"]

    output_mapping = {}
    for key in split_dict.keys():
        #lemma = line[0]
        values = split_dict[key]
        assert len(header) == len(values)
        output_mapping[key] = {}
        
        for (field, value) in zip(header, values):
            output_mapping[key][field] = value


    return output_mapping


def read_mapping(fname):
    data = readlist(fname)
    data = [line for line in data if not re.match("\A\s*\Z", line)] ## strip empties
    data = [line.split("\t") for line in data]
    for line in data:
        assert len(line) == len(data[0])
    header = data[0]
    header = header[1:] ## remove lemma's name
    data = data[1:]
    
    mapping = {}
    for line in data:
        lemma = line[0]
        values = line[1:]
        mapping[lemma] = {}
        for (key, value) in zip(header, values):
            mapping[lemma][key] = value

    return mapping



def make_htk_wildcards(n):
    """
    HTK wildcards allow item sets like {*/feature:?/*,*/feature:1?/*}
    to express "feature < 20" in question definitions. For a given integer 
    max value n, return a list of strings with HTK wildcards matching non-negative
    integers less than n. 

    E.g.: make_htk_wildcards(236) gives:
    ['?', '??', '1??', '20?', '21?', '22?', '230', '231', '232', '233', '234', '235']
   
    """
    assert type(n)==int
    assert n >= 0
    patts = []
    first_place = True
    for place in range(len(str(n))):
        place_value = int(str(n)[place])
        stem = str(n)[:place]
        wildcard_length = len(str(n)) - place - 1
        covered = range(0, place_value)
        if first_place: 
            for sublength in range(1, wildcard_length):
                patt = stem +          (sublength * "?")    
                patts.append( patt )            
        for i in covered:
            if first_place and i==0: 
                if len(str(n)) == 1: ## for single digit n, include "0":
                    patt = stem +  str(i) + (wildcard_length * "?")
                else: # strip leading zeros:                
                    patt = stem +          (wildcard_length * "?")    
            else:
                patt = stem +  str(i) + (wildcard_length * "?")
            patts.append( patt )     
        first_place = False
    return patts

p = make_htk_wildcards(6)



## These 2 were in Utterance.py:
def fix_data_type(data):
    """
    Turn the data into int if possible, then a float, else a unicode
    """
    try:
        converted_data = int(data)
    except ValueError:
        try:
            converted_data = float(data)
        except:
            converted_data = unicode(data) 
    return converted_data
#
def final_attribute_name(xpath):
    """
    Find the final text element of an xpath which we will assume is the name
    of an attribute.    
    
    TODO: find a better and less error-prone way to do this!
    """
    if type(xpath) == XPath: ## in case compiled:
        pathstring = xpath.path
    else:
        pathstring = xpath
    fragments = re.split("[/:@\(\)]+", pathstring)  
    return fragments[-1]    
    
def add_htk_header(datafile, floats_per_frame, frameshift_ms):
        """
        Add HTK header (for user-specified format -- 9) to some data in-place
        
        From the HTKBook, p.69:
             nSamples   -- number of samples in file (4-byte integer)
             sampPeriod -- sample period in 100ns units (4-byte integer)
             sampSize   -- number of bytes per sample (2-byte integer)
             parmKind   -– a code indicating the sample kind (2-byte integer)

        """
        filesize = os.stat(datafile).st_size
        framesize = 4 * floats_per_frame        
        if filesize % float(framesize) != 0:
            sys.exit('add_htk_header: not valid framesize (%s floats)'%(floats_per_frame))
        nframe = filesize / framesize
        header = struct.pack('iihh', nframe, ms_to_htk(frameshift_ms), framesize, 9)

        f = open(datafile, 'rb')
        data = f.read()
        f.close()

        ## overwrite existing data:
        f = open(datafile, 'wb')
        f.write(header)
        f.write(data)
        f.close()

def read_htk_header(datafile):
        """
        Read HTK header of datafile, return ...
        
        From the HTKBook, p.69:
             nSamples   -- number of samples in file (4-byte integer)
             sampPeriod -- sample period in 100ns units (4-byte integer)
             sampSize   -- number of bytes per sample (2-byte integer)
             parmKind   -– a code indicating the sample kind (2-byte integer)

        """
        header_pattern = 'iihh'
        header_size = struct.calcsize(header_pattern)
        with open(datafile, mode='rb') as f: 
            data = f.read(header_size)
        unpacked = struct.unpack(header_pattern, data)
        return unpacked
        
def get_htk_filelength(datafile):
        """
        parse the header of datafile, then return legnth of data according to header in seconds
        """
        (samples, period, sample_size, param_type) = read_htk_header(datafile)
        ms_period = htk_to_ms(period)
        ms_length = ms_period * samples
        sec_length = ms_length / 1000.0
        return sec_length
 
 

        
def write_bash_config(dict_like, fname):
    """
    Write keys & values in dict_like (e.g. ConfigObj) to file to be read as bash config.
    ConfigObj only writes .ini style files. Basically, remove space around = and add double 
    quotes.
    """
    f = open(fname, 'w')
    for (k,v) in dict_like.items():
        f.write('%s="%s"\n'%(k,v))
    f.close() 
    
def str2bool(s):
    '''
    Conversion of config values without whole configspec malarkey
    
    as_bool not satisfactory as can't combine with default values,
    resulting in e.g. (in scripts/processors/BasicTokenisers.py):
    
        try:
            self.add_terminal_tokens = self.config.as_bool('add_terminal_tokens')
        except KeyError:
            self.add_terminal_tokens = False
    
    '''
    if type(s) in [str, unicode]:
        s = s.strip(' \n')
        if s in ['True', 'yes']:
            return True
        elif s in ['False', 'no']:
            return False
        else:
            sys.exit('str2bool: bad value for conversion to boolean: %s'%(s))
    elif type(s) == bool:
        return s
    else:
        sys.exit('str2bool: input must be string, unicode or bool')    
        