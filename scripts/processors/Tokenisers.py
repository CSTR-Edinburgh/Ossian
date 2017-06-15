#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

#from naive.naive_util import *
import unicodedata
import glob
from processors.UtteranceProcessor import SUtteranceProcessor, Element
# from processors.NodeSplitter import *
# from processors.NodeEnricher import *
import datetime
from naive import naive_util

try:
    import regex as new_regex
except ImportError:
    sys.exit('Please install "regex": https://pypi.python.org/pypi/regex ')
    
import default.const as c

class RegexTokeniser(SUtteranceProcessor):
    '''
    A very crude tokeniser, which:

    1. splits text with a regular expression specified
    in config file, which defaults to whitespace. Note that whether spaces etc. are 
    treated as tokens or not depends on use of brackets in the regex -- cf. (\s+) and \s+

    2. optionally

    3. classifies tokens on the basis of regex

    4. optionally add safetext representation
    '''
    def __init__(self, processor_name='regex_tokeniser', target_nodes = '//utt', split_attribute = 'text', \
                child_node_type = 'token', add_terminal_tokens=True, split_pattern='\s+', \
                add_token_classes = True, \
                class_patterns = [('space', '\A\s+\Z'), ('punctuation', '\A[\.\,\;\!\?\s]+\Z')], \
                default_class = 'word', class_attribute='token_class',
                add_safetext = True,
                safetext_attribute = 'safetext', 
                lowercase_safetext = True):

        self.processor_name = processor_name

        self.split_pattern = split_pattern
        self.target_nodes = target_nodes
        self.split_attribute = split_attribute
        self.child_node_type = child_node_type
        self.add_terminal_tokens = add_terminal_tokens
        self.class_patterns = [(name, new_regex.compile(patt)) for (name, patt) in class_patterns]
        self.default_class = default_class
        self.class_attribute = class_attribute
        self.add_token_classes = add_token_classes

        self.add_safetext = add_safetext
        self.safetext_attribute = safetext_attribute
        self.lowercase_safetext = lowercase_safetext

        self.regex = new_regex.compile(self.split_pattern)
        
        super(RegexTokeniser, self).__init__()


    def process_utterance(self, utt):

        #print 'target nodes: %s'%(utt.xpath(self.target_nodes))
        for node in utt.xpath(self.target_nodes):
            assert node.has_attribute(self.split_attribute)
            to_split = node.get(self.split_attribute)
            
            child_chunks = self.splitting_function(to_split)
            
            for chunk in child_chunks:
                #print '=='
                #print chunk
                child = Element(self.child_node_type)
                child.set(self.split_attribute, chunk)

                if self.add_token_classes:
                    token_class = self.classify_token(chunk)
                    #print token_class
                    child.set(self.class_attribute, token_class)

                if self.add_safetext:
                    token_safetext = self.safetext_token(chunk)
                    child.set(self.safetext_attribute, token_safetext)

                node.add_child(child)

    def classify_token(self, token):

        ## Special handling of terminal token:
        if token == c.TERMINAL:
            return c.TERMINAL
        for (item_class, pattern) in self.class_patterns:
            if pattern.match(token):
                return item_class
        ## if we have got this far, none of patterns matched -- return default:
        return self.default_class

    def safetext_token(self, instring):

        ## Special handling of terminal token:
        if instring == c.TERMINAL:
            return c.TERMINAL
        else:
            if self.lowercase_safetext == 'True':
                return naive_util.safetext(instring.lower())
            else:
                return naive_util.safetext(instring)        

    def splitting_function(self, instring):
        tokens = self.regex.split(instring)
        tokens = [t for t in tokens if t != '']
        if self.add_terminal_tokens:
            tokens = [c.TERMINAL] + tokens + [c.TERMINAL]
        return tokens 
        
    def do_training(self, speech_corpus, text_corpus):
        print "RegexTokeniser requires no training"    


'''
http://www.fileformat.info/info/unicode/category/index.htm:

Code    Description
[Cc]    Other, Control
[Cf]    Other, Format
[Cn]    Other, Not Assigned (no characters in the file have this property)
[Co]    Other, Private Use
[Cs]    Other, Surrogate
[LC]    Letter, Cased
[Ll]    Letter, Lowercase
[Lm]    Letter, Modifier
[Lo]    Letter, Other
[Lt]    Letter, Titlecase
[Lu]    Letter, Uppercase
[Mc]    Mark, Spacing Combining
[Me]    Mark, Enclosing
[Mn]    Mark, Nonspacing
[Nd]    Number, Decimal Digit
[Nl]    Number, Letter
[No]    Number, Other
[Pc]    Punctuation, Connector
[Pd]    Punctuation, Dash
[Pe]    Punctuation, Close
[Pf]    Punctuation, Final quote (may behave like Ps or Pe depending on usage)
[Pi]    Punctuation, Initial quote (may behave like Ps or Pe depending on usage)
[Po]    Punctuation, Other
[Ps]    Punctuation, Open
[Sc]    Symbol, Currency
[Sk]    Symbol, Modifier
[Sm]    Symbol, Math
[So]    Symbol, Other
[Zl]    Separator, Line
[Zp]    Separator, Paragraph
[Zs]    Separator, Space
'''        

# class SafeTextMaker(NodeEnricher):
#     '''Lowercase, convert to ascii-safe strings, but handle terminal token specially'''
#     def load(self):
#         NodeEnricher.load(self)
#         self.lowercase = self.config.get('lowercase', 'True')  ## string not bool
    









# class RegexClassifier(NodeEnricher):
#     '''Classifies nodes based on comparing their input_attribute against a sequence
#     of classes and associated regular expressions. The sequence is specified in
#     a config subsection. The sequence is iterated through, when a pattern is matched
#     the search stops and the class corresponding to the matched pattern is assigned to 
#     the node under output_attribute. If none are matched, default_class is assigned.'''
#     def load(self):
#         NodeEnricher.load(self)
      
#         if 'classes' not in self.config:
#             sys.exit('Please specify classes for RegexClassifier')
#         self.classes = self.config['classes']  
#         if 'default_class' not in self.config:
#             sys.exit('Please specify default_class for RegexClassifier')
#         self.default_class = self.config.get('default_class')  
    
# #         token_classes = config_list(self.config.get('token_classes', ['space','not_space']))
# #         token_class_patterns = config_list(self.config.get('token_class_patterns', ['\s+']))
# #         print token_classes
# #         print token_class_patterns
# #         assert len(token_classes) == (len(token_class_patterns) + 1),'One more class must be \
# #                                             given than patterns, as the default case'
                                            
                                            
#         ## Compile on load, adding string-end symbols:
#         self.class_patterns = [(name, new_regex.compile('\A%s\Z'%(string))) \
#                 for (name, string) in self.classes.items()]
    
#     # def enriching_function(self, instring):
        

#     def do_training(self, speech_corpus, text_corpus):
#         print "RegexTokeniser requires no training"    


#     def do_training(self, speech_corpus, text_corpus):
#         print "RegexTokeniser requires no training"    
    


 
        # 
# class CharClassTokenClassifier(NodeEnricher):
#     '''Classifies token based on list of classes and associated regular expresssions.'''
#     def load(self):
#         token_classes = config_list(self.config.get('token_classes', ['space','not_space']))
#         token_class_patterns = config_list(self.config.get('token_class_patterns', ['\s+']))
#         print token_classes
#         print token_class_patterns
#         assert len(token_classes) == (len(token_class_patterns) + 1),'One more class must be \
#                                             given than patterns, as the default case'
#         ## Split classes into ones with patterns and default:
#         self.token_classes = token_classes[:-1]
#         self.default_token_class = token_classes[-1]
#         ## Compile on load, adding string-end symbols:
#         self.token_class_patterns = [re.compile('\A%s\Z'%(string)) for string in token_class_patterns]
#         
#     def classify(self, instring):
#         ## Special handling of utterance end token:
#         if instring == c.UTTEND:
#             return c.UTTEND
#         for (token_class, pattern) in zip(self.token_classes, self.token_class_patterns):
#             if re.match(pattern, instring):
#                 return token_class
#         ## if we have got this far, none of patterns matched -- return default:
#         return self.default_token_class
# 
#     def train(self):
#         print "RegexTokeniser requires no training"    
#         
#        
# 
# class CharClassTokeniser(NodeSplitter):
#     '''
#     Simple tokeniser which relies on characer classes, which can be specified using Unicode
#     character properties, to split text into tokens.
# 
#     Depend on https://pypi.python.org/pypi/regex, a "new regex implementation [which] is 
#     intended eventually to replace Python's current re module implementation"
#     '''
# 
#     def load(self):  
# 
#         NodeSplitter.load(self)
#         self.split_pattern = self.config.get('split_pattern', '\s+')
#         
# 
# 
#         
#         
#         if 'character_classes' not in self.config:
#             sys.exit("List of character classes must be specified for CharClassTokeniser")
#         self.character_classes = self.config['character_classes']
#         for (name, pattern) in self.character_classes.items():
#             self.split_pattern = self.split_pattern.replace(name, pattern)
#         
#         self.regex = new_regex.compile(self.split_pattern, new_regex.UNICODE)
#         
#     def splitting_function(self, instring):
#         tokens = new_regex.split(self.regex, instring)
#         tokens = [t for t in tokens if t != '']
#         if self.add_terminal_tokens:
#             tokens = [c.UTTEND] + tokens + [c.UTTEND]
#         return tokens 
#         
#     def do_training(self, speech_corpus, text_corpus):
#         print "CharClassTokeniser requires no training"    
# 
# 


# class TweakedCharPropTokeniser(NodeSplitter):
#     '''
#     As CharPropTokeniser , but allow user to modify char classes by editing a character table
#     '''
        
        
        
        
# #     def __init__(self, table_file, character_class_precedence, \
# #                 character_class_patterns, tokeniser_split_pattern):  
# # 
# #         self.table = {}   ## This table starts empty but can be populated by training
# # 
# #         self.table_file = table_file
# #         self.character_class_precedence = character_class_precedence
# #         self.character_class_patterns = character_class_patterns
# #         self.tokeniser_split_pattern = tokeniser_split_pattern
# # 
# #         assert len(self.character_class_precedence) == len(self.character_class_patterns)
# #         self.character_classes = dict(zip(self.character_class_precedence, self.character_class_patterns))
# # 
# #         self.unicode_category_map = {}  ## will map: coarse categories->regex
# #         self.populate_unicode_category_map()
# # 
# #         # table data has already been collected, load it from file:
# #         if os.path.isfile(table_file):    
# #             self.populate_table_from_file(table_file)
# #             
# #         if self.table != {}:
# #             self.compile_regex()


#     ## OSW TODO: similar to function in LookupTable -- combine them?
#     ## Differences: here, get header from first line
#     def populate_table_from_file(self, fname):
#         data = readlist(fname)
#         data = [re.split("\t", line) for line in data]

#         if data == []:
#             print "warning: no data loaded from table"
#             pass
#         else:
#             self.header_line = data[0]
#             header = self.header_line[1:]

#             for line in data[1:]:
#                 assert len(line) == len(header)+1
#                 lemma = line[0]

#                 ## handle tab replacements:
#                 if "\\t" in lemma:
#                     lemma = lemma.replace("\\t", "\t")
                
#                 self.table[lemma] = {}
#                 for (key, value) in zip(header, line[1:]):
#                     self.table[lemma][key] = value



#     def compile_regex(self):
#         self.split_regex_string = self.tokeniser_split_pattern
#         interpolated_regex = self.interpolate_split_regex()    
#         self.split_regex = re.compile(interpolated_regex, re.UNICODE)



#     def tokenise(self, data):
#         chunks = re.split(self.split_regex, data)
#         ## The empty string might be in chunks -- filter:
#         chunks = [chunk for chunk in chunks if chunk != ""]      
#         return chunks



#     def tokenise_to_string(self, data, delimiter="___"):
#         assert delimiter not in data,"Problem in tokenise_to_string: delimiter '%s' occurs in input string '%s'"%(delimiter, data)
#         tokens = self.tokenise(data)
#         tokens = delimiter.join(tokens)
#         return tokens



#     def tokenise_textfiles(self, fnames_in, fname_out, strip_classes=[], token_unit="word"):
#         """
#         Take a list utf-8 textfile fnames_in, read 1 line at a time, and do the following:
#             --tokenise
#             --convert to safetext
#             --strip tokens in strip_classes (if any)
#         Write accumulated data to fname_out, whitespace-delimiting the tokens
#         """
#         #print "Tokenising text corpus..."
#         f_out = open(fname_out, "w")
#         i = 0
#         for fname_in in fnames_in:
#             f_in = codecs.open(fname_in, encoding='utf-8')
#             for line in f_in:
#                 line = line.strip(" \n\r")
#                 if in_unicode_table(line):
#                     if token_unit == "word":
#                         line = self.tokenise(line)              
#                     elif token_unit == "letter":
#                         line = list(line)
#                     else:
#                         print "token_unit '%s' not recognised"%(token_unit)
#                     line = [token for token in line if self.token_class(token) not in strip_classes]               
#                     line = [self.safetext(token) for token in line]               
#                     line = " ".join(line) + "\n"
#                     f_out.write(line)
#                 else:
#                     print "Tokenising text corpus: skip line -- can't find a character in unicode database"
#                     try:
#                         print line
#                     except UnicodeEncodeError:
#                         print "[line not printable]"  ## Added because got error on a French corpus: 
#                                                         ## UnicodeEncodeError: 'charmap' codec can't encode
#                                                         ## character u'\xef' in position 61: character maps to <undefined>

#                 i += 1
#                 if i % 10000 == 0:
#                     print ".",
#             f_in.close()
#         f_out.close()
        



                                
#     def train(self, text_list):
#         '''
#         Provided with a list of text files (a sample of the 
#         sort of text a TTS system might encounter), safetext and character_class
#         will be precomputed for all character types appearing in the sample. 
#         This will probably improve efficiency, but more importantly it lets a 
#         user visually check the values to make sure they are sensible, and alter
#         as necessary.
#         '''

#         assert len(text_list) > 0,"No transcriptions exist"
        
#         character_counts = {}
        
#         ## Count character types in text:
#         #print "Learning character table..."
#         i = 0
#         for text_file in text_list:
#             text = readlist(text_file, check_unicode_database=True)            
#             for line in text:    
#                 i += 1
#                 if i % 10000==0:
#                     print ".",
#                 for character in line:   
#                     if character not in character_counts:
#                         character_counts[character] = 0
#                     character_counts[character] += 1    
                   
#         ## Precompute safetext and coarse categories, store in self.table:
#         for (character, count) in character_counts.items():
          
#             self.add_to_table(character, frequency=count)
     
#         ## reload self to get regex patterns compiled:
#         self.compile_regex()


#     def save(self):

#         if self.table != {}:

#             ## rewrite tabs as strings:
#             for (key,value) in self.table.items():
#                  if "\t" in key:
#                     key = key_replace("\t", "\\t")

#             text_table = flatten_mapping(self.table,  \
#                     sort_by=["character_class", "frequency"], reverse_sort=True)

#             text_table = [key + "\t" + value for (key, value) in text_table]
#             writelist(text_table, self.table_file, uni=True)


#     def add_to_table(self, character, frequency=0):
#         ## TODO:  private and public character_class() etc -- 

#         assert type(character) == unicode

#         safetext = self.safetext(character)
#         character_class = self.character_class(character)        
#         ## date-stamp entries so we know when stuff is added (hours?)
#         added_on =  str(datetime.date.today()) 

#         self.table[character] = {"safetext": safetext,
#                                  "character_class": character_class,
#                                  "added_on": added_on,
#                                  "frequency": frequency}


#     def display_table(self):
#         for (key, value) in self.table.items():
#             print "%s %s"%(key, value)


#     def alert_user(self):
        
#         print """
#         Lists of letters and punctuation written to 
#         %s and 
#         %s. 
#         Check and adjust
#         manually before continuing. ASCII substitutions are given -- keep these
#         HTK etc. compatible. Assume that all separators will be matched by
#         regex \s -- i.e. don't list them explicitly.
#         """%(letter_fname, punc_fname)
            
        
#     def populate_unicode_category_map(self):
#         '''
#         Look at self.config['character_classes'] which contains coarse categories 
#         as keys and regex as values. From this an a list of all unicode categories,
#         make self.unicode_category_map, which  maps from all legal fine unicode
#         categories to coarse category.
#         '''
        
#         # For listing of unicode categories, see e.g. http://www.fileformat.info/info/unicode/category/index.htm
#         unicode_categories = ['Cc', 'Cf', 'Cn', 'Co', 'Cs', 'LC', 'Ll', 'Lm', 'Lo', \
#                               'Lt', 'Lu', 'Mc', 'Me', 'Mn', 'Nd', 'Nl', 'No', 'Pc', \
#                               'Pd', 'Pe', 'Pf', 'Pi', 'Po', 'Ps', 'Sc', 'Sk', 'Sm', \
#                               'So', 'Zl', 'Zp', 'Zs']
#         # Map all unicode categories to a coarse class whose regular expression matches 
#         # it. Where there are multiple matches, take the last in list:                      
#         for code in unicode_categories:
#             for (coarse_class, regex) in self.character_classes.items():
#                 if re.match(regex, code):
#                     self.unicode_category_map[code] = coarse_class
        


#     def character_class(self, unicode_string):
#         '''
#         Get the coarse class (e.g. punc) for a unicode character. Try lookup in self.table,
#         if it is a new character, look up category in unicodedata and convert to coarse 
#         class. 
#         '''
        
#         assert len(unicode_string) == 1,'''Method character_type can only be used on 
#                                             single characters'''
#         if unicode_string in self.table:
#             return self.table[unicode_string]['character_class']
#         else:
#             ## Look up unicode category in unicode data then translate to coarse class:   
#             try:                                     
#                 cclass = unicodedata.category(unicode_string)                     
#             except:
#                 print 'Could not get a category for %s from unicodedata'%(unicode_string)
#                 sys.exit(1)
#             assert cclass in self.unicode_category_map,'Category %s not in map'%(cclass)
#             return self.unicode_category_map[cclass]
            
            
#     def token_class(self, unicode_string):
#         '''
#         Assign a class to a token (sequence of characters) based on the classes of its
#         constituent characters.  character_class_precedence determines what the token's
#         class will be. 
        
#         TODO: explain and motivate precedence.
#         '''
#         ## Get classes of letters in the token:
#         classes = [self.character_class(char) for char in unicode_string]
#         for character_type in self.character_class_precedence:
#             if character_type in classes:
#                 return character_type

#          ### Was originally this:
# #        # If we get this far, the loop was not broken by return -- error:
# #        print 'No token class found for token %s'%(unicode_string)
# #        sys.exit(1)
#         ### ... but this is not robust enough against weird characters -- choose some 
#         ### arbitrary value instead:

#         return self.character_class_precedence[0] ## return arbitrary value


            
            
#     def safetext(self, unicode_string):
#         safetext = ''
#         for char in unicode_string:
#             if char in self.table:
#                 safetext += self.table[char]['safetext']
#             else:
#                 safetext += self.unicode_character_to_safetext(char)    
#         return safetext
        

#     def unicode_character_to_safetext(self, char):
#         '''
#         Return value from self.table if it exists, otherwise work one out. The substitute 
#         should be safe to use with applications of interest (e.g. in HTK modelnames), and
#         a perhaps over-cautious subset of ASCII is used for this (uppercase A-Z).
        
#         TODO: [make this explanation complete]
        
#          To enable 
#         reverse mapping, multicharacter safetexts are delimited with _. 
        
#         TODO: Simultaneously map to lowercase -- move this elsewhere? Optional? 
#         '''
#         ## Replacements to make greedily within unicode name:
#         name_reps = {" ": "",
#                      "-": "",
#                      "0": "ZERO",
#                      "1": "ONE",
#                      "2": "TWO",
#                      "3": "THREE",
#                      "4": "FOUR",
#                      "5": "FIVE",
#                      "6": "SIX",
#                      "7": "SEVEN",
#                      "8": "EIGHT",
#                      "9": "NINE"     }
#         if char.lower() in list("abcdefghijklmnopqrstuvwxyz"):
#             substitute = char.lower()
#         else:                
#             try:
#                 substitute = unicodedata.name(char.lower())
#             except ValueError:   ## got ValueError: no such name
#                 substitute = "PROBLEM CHARACTER"
#             for key in name_reps.keys():
#                 substitute = substitute.replace(key, name_reps[key])
#             substitute = "_" + substitute + "_"    
#         return substitute


#     def character_class_regex_dict(self):
#         """
#         Get a dict mapping character_class names to regex strings to match one
#         instance of that class.
#         """
#         outdict = {}
#         for char_class in self.character_class_precedence:
#             outdict[char_class] = self.character_class_regex(char_class)
            
#         return outdict

#     def character_class_regex(self, character_class):
#         """
#         Return a string that will be compiled into regex for matching 1 occurance of 
#         any memeber of character_class (as given in character_class of self.table).
        
#         NOTE: this won't handle OOV characters --- they need to be added to table first.

#         What would really be good here is proper unicode regular expressions (
#         allowing matching on unicode properties: see e.g. 
#         http://www.regular-expressions.info/unicode.html)

#         """
#         pattern = u""
#         assert self.table != {},"CharacterTable's table must have entries to compile a character_class_regex\nTry the train() method"
#         for character in self.table.keys():
#             if self.table[character]["character_class"] == character_class:
#                 pattern += character # .decode("utf-8")    
#         pattern = re.escape(pattern) ## Deal with literals of regex special characters
#         pattern = "[" + pattern + "]"
#         return pattern

#     def interpolate_split_regex(self):
#         class_dict = self.character_class_regex_dict()
#         interpolated_regex = unicode(self.split_regex_string)

#         for (name, wildcard) in class_dict.items():       
#             interpolated_regex = interpolated_regex.replace(unicode(name), wildcard)
#         return interpolated_regex             

