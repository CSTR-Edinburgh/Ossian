#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

from main.Utterance import *
import copy
import string
from lxml import etree

"""
General functions that operate on nodes of utterances (to e.g. add children, restructure subtrees, 
apply arbitrary functions to create a new attribute from an existing one).

"""

def enrich_nodes(node, function=string.upper,\
                     target_nodes="//Token", input_attribute="text", \
                     output_attribute="uppercase_text", overwrite=True, kwargs={}):
    """
    Apply function to elements of utt that mathc xpath target_nodes. Input to
    the function with be input_attribute, output will be put in output_attribute.  

    Using the defaults, this should make uppercase copies of tokens [TODO: test this].  
    """
    nodes = node.xpath(target_nodes)
    assert len(nodes) > 0
    for node in nodes:
        assert node.has_attribute(input_attribute)
        if not overwrite:
            assert not node.has_attribute(output_attribute),"Cannot overwrite existing '%s' in node "%(output_attribute)
        input_data = node.get(input_attribute)
        transformed_data = function(input_data, **kwargs)
        node.set(output_attribute, transformed_data)


def add_children(node, child_tag="Token", parent_attribute="text", \
                             delimiter=" ", child_attribute="text", skip=[]):
    """
    Split contents of node's parent_attribute on delimiter, make children
    of node with tag child_tag and add split contents of parent_attribute
    as child_attribute, one chunk per child.

    Using the defaults, this provides very crude tokenisation on whitespace. 
    """
    ## add lookahead and lookbehind to delimiter to stop it matching at ends 
    ## of utterance: splitting the line (from Candide) "_O che sciagura d' essere senza coglioni!"
    ## resulted in an empty due to initial _
    delimiter_patt = re.compile("(?<=.)%s(?=.)"%(re.escape(delimiter)))
    assert node.has_attribute(parent_attribute)
    data = node.get(parent_attribute)
    child_chunks = re.split(delimiter_patt, data)
    for chunk in child_chunks:
        

        if chunk not in skip:

            child = Element(child_tag)
            child.set(child_attribute, chunk)
            node.add_child(child)


def add_syllable_structure(node, pronunciation, syllable_delimiter='|', syllable_tag='syllable', phone_tag='segment',\
                            pronunciation_attribute='pronunciation', stress_attribute='stress'):
    '''
    Take pronunciations in this form:
        "k w ay1 | ax0 t | n ax0 s"
    Add syllables and segments under the node, and break off stress marks as separate syllable feature like this:

    '''
    sylls = re.split('\s*%s\s*'%(re.escape(syllable_delimiter)), pronunciation)
    for syll in sylls:
        phones = re.split('\s+', syll)
        clean_phones = []
        stress_marks = []
        for phone in phones:
            if phone == '':
                contine
            if phone.endswith('0') or phone.endswith('1') or phone.endswith('2'):
                stress_marks.append(phone[-1])
                phone = phone.strip('012')
            clean_phones.append(phone)
        if len(stress_marks) == 0:
            print 'WARNING: no stress mark in syllable "%s"'%(syll)
            stress_marks = ['0']
        elif len(stress_marks) > 1:
            print 'WARNING: multiple stress marks in syllable "%s" -- take the first'%(syll)
        stress = stress_marks[0]
        syll_node = Element(syllable_tag)
        syll_node.set(pronunciation_attribute, syll)
        syll_node.set(stress_attribute, 'stress_'+stress)
        node.add_child(syll_node)
        for phone in clean_phones:
            phone_node = Element(phone_tag)
            phone_node.set(pronunciation_attribute, phone)
            syll_node.add_child(phone_node)




def add_end_padding(node, **padding_attributes):

    ## Make a padding node:
    other_attributes = copy.copy(padding_attributes)
    del other_attributes["tag"]
    padding = Element(padding_attributes["tag"], other_attributes)   

    ## Insert copies at beginning and end of utterance:
    node.insert(0, copy.copy(padding))
    node.append(copy.copy(padding))



def do_lex_lookup(node, target_nodes="//Token", lexicon=None):
    """
    Use the lexicon to add pronunciation(s) to the node. Handle punctuation and
    space tokens specially.
    """
    nodes = node.xpath(target_nodes)
    assert len(nodes) > 0
    for node in nodes: 
        if node.get("token_class") == "punc":
            pronunciation = "sil, skip"             

        elif node.get("token_class") == "space":
            pronunciation = "skip, sil" 
        elif node.get("token_class") == "letter":
            pronunciation = lexicon.lookup(node.get("safetext"))
        elif  node.get("token_class") == "utt_end":
            pronunciation = "sil"  ## don't allow skip at utt end, else:
                            ##  ERROR [+7332]  CreateInsts: Cannot have Tee models at start or end of transcription
        else:
            print "do_lex_lookup can't handle token_class %s"%(node.get("token_class"))
            sys.exit(1)

        node.set("pronunciation", pronunciation)

def add_segments_from_label(utt, input_label='time_lab', target_nodes='//Token', \
                    target_attribute='safetext'):

    """         
    Function to merge times and force-aligned segments from e.g.
    force-aligned label file into the voice's current utterance structure.
    
    To this end, do the following tasks:
    
    1) Scan target_nodes, and check they are consistent with the lines of the time_lab
    
    2) Where a node has an associated HMM model *not* named with the constant
    SKIP_MODEL_NAME, add pronunciation, start and end attributes (NB: hard-coded names).
    
    Where a node is associated with an HMM model named SKIP_MODEL_NAME, remove that node.
    
    TODO: variable names are misleading (still older 'token_node', not general 'node')
    """

    ## Find associated label file and read label data:
    labfile = utt.get_filename(input_label)                       
   
    label = read_htk_label(labfile)

    ## Get lists of words and segments from label:
    label_tokens = []
    label_segments = [] ## list of lists
    token_segments = [] ## list of segments for 1 token, entry in label_segments

    for (start, end, segment, token) in label:
        if token != "":
            if token_segments != []: ## i.e. for first line of label
                label_segments.append(token_segments)
            token_segments = [] ## re-init for this new token
            label_tokens.append(token)
        token_segments.append((start, end, segment)) 
    label_segments.append(token_segments) ## entry for final word

    assert len(label_tokens) == len(label_segments)
    
    ## Sanity check label is consistent with what is in utt structure: 
    ## 1) Do lengths match?       
    utt_tokens = utt.xpath(target_nodes)

    assert len(label_tokens) == len(utt_tokens),"Label\
                                and utt contain diffent numbers of tokens"
    
    ## 2) Do individual token items correspond?
    for (utt_token, lab_token) in zip(utt_tokens, label_tokens):
        if lab_token == utt_token.get(target_attribute):
            pass
        else:
            print "Labels and utt content do not match"
            sys.exit(1)    

    ### Now overwrite target_attribute in the target_nodes with names of segments in labels,
    ### and add times; delete skipped nodes:                 
    for (token_node, seg_list) in zip(utt_tokens, label_segments):
    
        assert len(seg_list) == 1 ## previously, worked with words, now with letters,
                                ## each should only have 1 phone name 
    
        ## Get back to actual letters in  case of e.g. _PUNC_ --> sil.
        ## This will need to be changed if we are to use real lexicon,
        ## unless the lexicon is aligned with e.g. epsilons for silent letters
#            safe_letter_list = burst_safestring(token_node.get("safetext"))
#            print safe_letter_list
#            print seg_list

        seg_names = [name for (start, end, name) in seg_list]
        chosen_pronunciation = " ".join(seg_names)

        (start, end, modelname) = seg_list[0]
                      
        if modelname != c.SKIP_MODEL_NAME:
            token_node.set(target_attribute, modelname)    
            token_node.set('start', str(start)) 
            token_node.set('end', str(end)) 
        else:
            token_node.getparent().remove(token_node)  ## delete the node
       


### version adding 'model' nodes:-
#                     
#         if modelname != c.SKIP_MODEL_NAME:
#         
#             ## Make new node for the model:
#             model = Element('model')
#         
#             model.set('pronunciation', modelname)    ### TODO: pronunciation hard coded!
#             model.set('start', str(start)) 
#             model.set('end', str(end)) 
#             
#             token_node.add_child(model)
#             

def add_segments_and_states_from_label(utt, input_label='time_lab', target_nodes='//Token', \
                    target_attribute='safetext', skippables=['_SPACE_','_PUNC_']):

    """         
    Function to merge times and force-aligned segments and states from
    force-aligned label file into the voice's current utterance structure.
    """
    labfile = utt.get_filename(input_label)                       
   
    label = read_htk_state_label(labfile)

    words = [line[1] for line in label]
    
    
    ## Sanity check label is consistent with what is in utt structure: 
    ## 1) Do lengths match?       
    utt_tokens = [node.attrib[target_attribute] for node in utt.xpath(target_nodes)]
    
    filtered_words = [w for w in words if w not in skippables]
    filtered_utt_tokens = [w for w in utt_tokens if w not in skippables]

    #print filtered_words
    #print filtered_utt_tokens

    assert len(filtered_words) == len(filtered_utt_tokens),"Label\
                                and utt contain diffent numbers of tokens"
    assert filtered_words == filtered_utt_tokens,"Label\
                                and utt contain diffent tokens"

    utt_tokens = utt.xpath(target_nodes)


    ## make padded labels with SKIP on skipped lines
    padded_labels = []
    l = 0
    u = 0                            
    while l < len(label):
        
        (seg, word) = label[l][:2]
        states = label[l][2:]
        if word == utt_tokens[u].attrib[target_attribute]:
            padded_labels.append(label[l])
            u += 1
            l += 1
        else:
            assert utt_tokens[u].attrib[target_attribute] in skippables
            padded_labels.append('SKIP')
            u += 1

    ##  more utt tokens to go? This can happen when e.g. final _END_ is skipped.
    while u < len(utt_tokens):
        assert utt_tokens[u].attrib[target_attribute] in skippables
        padded_labels.append('SKIP')
        u += 1


    if len(padded_labels) != len(utt_tokens):
        utt_tokens_strings = [etree.tostring(node) for node in utt_tokens]
        print "padded_labels and utt_tokens don't match:"
        for pair in zip(padded_labels, utt_tokens_strings):
            print pair
        print (len(padded_labels),  len(utt_tokens))
        print "padded_labels and utt_tokens don't match"
        sys.exit(1)


    ### Now overwrite target_attribute in the target_nodes with names of segments in labels,
    ### and add states and times; delete skipped nodes:                 
    for (token_node, label_line) in zip(utt_tokens, padded_labels):
    
        if label_line == 'SKIP':
            token_node.getparent().remove(token_node)  ## delete the node
        else:
            (seg, word) = label_line[:2]
            states = label_line[2:]
            token_node.set(target_attribute, seg)
            for [start,end,state] in states:
                state_node = Element('state')
                state_node.set('start', str(int(start)))
                state_node.set('end', str(int(end)))
                token_node.add_child(state_node)
                
                
 

def propagate_start_and_end_times_up_tree(utt):
    """
    Look for attributes 'start' and 'end' in leaf nodes of utt structure.
    Where a leaf has these, add these to ancestors all the way back to 
    root. If ancestors already have start and end attributes, these will
    be overwritten.
    """
    leaf_nodes_xpath = '//node()[not(node())]'
    leaves = utt.xpath(leaf_nodes_xpath)
    for leaf in leaves:
        ##leaf.pretty_print()
        if leaf.has_attribute('start') and leaf.has_attribute('end'):
            for ancestor in leaf.iterancestors():
                if not ancestor.has_attribute('start'):
                    ancestor.set('start', leaf.get('start'))
                else:
                    #print type(ancestor.get('start'))
                    #print type(leaf.get('start'))
                    if float(ancestor.get('start')) > float(leaf.get('start')):
                        ancestor.set('start', leaf.get('start'))
                #---
                if not ancestor.has_attribute('end'):
                    ancestor.set('end', leaf.get('end'))
                else:
                    if float(ancestor.get('end')) < float(leaf.get('end')):
                        ancestor.set('end', leaf.get('end'))                 
                #ancestor.pretty_print()
    

def propagate_silence_tag_up_tree(utt, target_nodes, target_attribute='pronunciation', \
                    silence_symbol='sil', output_attribute='has_silence'):
    #leaf_nodes_xpath = '//node()[not(node())]'   ### TODO: method of utt class
    leaves = utt.xpath(target_nodes)

    for leaf in leaves:

        ## First pass: set to default False where output doesn't exist already:
        for ancestor in leaf.iterancestors():
            if not ancestor.has_attribute(output_attribute):
                ancestor.set(output_attribute, 'no')
                
        ## 2nd pass: set to True where appropriate
        #print leaf
        #print leaf.attrib
        if leaf.has_attribute(target_attribute):                
            #print leaf.get(target_attribute) 
            #print silence_symbol
            #print '^^^^^^^'
            if leaf.get(target_attribute) == silence_symbol:
                for ancestor in leaf.iterancestors():
                    ancestor.set(output_attribute, 'yes')
           


def add_default_segments(utt):

    """         
    """     
    utt_tokens = utt.xpath("//Token")

    ## Add segment nodes as child of token, also times:                              
    for token_node in utt_tokens:

        ## Pick the first of possible pronunciations to use:
        pronunciations = token_node.get("pronunciation")
        pronunciations = pronunciations.split(", ")
        chosen_pronunciation = pronunciations[0]
        seg_list = chosen_pronunciation.split(" ")

        for modelname in seg_list:

            if modelname != "skip":
                letter_node = Element("Letter", modelname=modelname)                                       
                token_node.append(letter_node) 





# def remove_short_silent_segments(utt, target_nodes='//Token', \
#                     target_attribute='safetext',  min_silence_duration=0):
#     """
#     Remove segments called "sil" less than min_silence_duration ms long.
#     TODO: adjust neighbour start/end times after removing short segments.
#     """          
#     nodes = utt.xpath(target_nodes)
# 
#     for node in nodes:
#         if node.get("modelname") == "sil":
#             token = node.xpath("./ancestor::Token")[0]
#             if token.get("token_class") != "utt_end":
#                 length = int(node.get("end")) - int(node.get("start"))
#                 if length < int(min_silence_duration):
#                     node.getparent().remove(node) ## delete the segment
                


def remove_short_silent_segments(utt, target_attribute='segment_name', \
                    silence_symbol='sil',  min_silence_duration=0):
    """
    Remove segments called "sil" less than min_silence_duration ms long.
    TODO: adjust neighbour start/end times after removing short segments.
    TODO: (find a general way to) prevent end silences from being deleted.
    """          
    leaf_nodes_xpath = '//node()[not(node())]'  ## general XPATH expression to find leaves
    leaves = utt.xpath(leaf_nodes_xpath)

    ## Exclude end leaves to allow short silences at ends: 
    leaves = leaves[1:-1]  

    for leaf in leaves:
        if leaf.has_attribute(target_attribute):
            if leaf.get(target_attribute) == silence_symbol:
                if not leaf.has_attribute("start") or not leaf.has_attribute("end"):
                    sys.exit('Supposedly silent node has no start and/or end: %s'%leaf.pretty_print())
                length = int(leaf.get("end")) - int(leaf.get("start"))
                #print length
                #print min_silence_duration
                #print '----'
                if length < int(min_silence_duration):
                    leaf.getparent().remove(leaf) ## delete the segment

def remove_short_silent_segments2(utt, target_nodes, target_attribute='segment_name', \
                    silence_symbol='sil',  min_silence_duration=0):
    """
    V1 of this func only looked at leaaves -- broke for state alignment.
    
    Remove segments called "sil" less than min_silence_duration ms long.
    TODO: adjust neighbour start/end times after removing short segments.
    TODO: (find a general way to) prevent end silences from being deleted.
    """          
    leaves = utt.xpath(target_nodes)

    ## Exclude end leaves to allow short silences at ends: 
    leaves = leaves[1:-1]  

    for leaf in leaves:
        if leaf.has_attribute(target_attribute):
            if leaf.get(target_attribute) == silence_symbol:
                if not leaf.has_attribute("start") or not leaf.has_attribute("end"):
                    sys.exit('Supposedly silent node has no start and/or end: %s'%leaf.pretty_print())
                length = int(leaf.get("end")) - int(leaf.get("start"))
                if length < int(min_silence_duration):
                    leaf.getparent().remove(leaf) ## delete the segment




def add_phrase_tags(utt, target_xpath='//Token', silence_symbol='sil', \
                                        attribute_with_silence='segment_name'):
    """
    Add attribute "phrase_start" and "phrase_end" to target nodes, with values 'True' and 'False'
    
    target_xpath    : matches target nodes to which tags are to be added 
    silence_symbol  :  symbol used for silence
    attribute_with_silence :  attribute of some descendent of target which can be set to silence_symbol
    
    Tue 24 Feb 2015 17:18:28 GMT -- first and last regroup_nodes_of_type in
    an utt will always be given "phrase_start" and "phrase_end" tags respectively.
    To this end, initialise start_next and end_next as True, not False

    """
    ## Forwards pass to mark phrase starts
    start_next = True ## Start a phrase on the next token?
    for token in utt.xpath(target_xpath):   
        
        if start_next and silence_symbol not in token.xpath("./descendant::*/attribute::" + attribute_with_silence): 
            token.set("phrase_start", "True")
            start_next = False

        else:
            token.set("phrase_start", "False")
            
        #print '---'
        #print token.xpath("./descendant::*/attribute::" + attribute_with_silence)
        if silence_symbol in token.xpath("./descendant::*/attribute::" + attribute_with_silence):
            #print 'start next!'
            start_next = True



    ## Backwards pass to mark phrase ends
    end_next = True ## Start a phrase on the 'next' token (i.e. the previous token in speaking order)?
    for token in reversed(utt.xpath(target_xpath)):      
        if end_next and silence_symbol not in token.xpath("./descendant::*/attribute::" + attribute_with_silence): 
            token.set("phrase_end", "True")
            end_next = False
        else:
            token.set("phrase_end", "False")
            
        if silence_symbol in token.xpath("./descendant::*/attribute::" + attribute_with_silence):
            #print 'end next!'
            end_next = True




def restructure(node, regroup_nodes_of_type="Token", \
            start_criterion="phrase_start", end_criterion="phrase_end", \
            new_parent_type="Phrase" ):
    """
    Group children of 'old_parent' of type 'regroup_nodes_of_type' under new
    nodes with the tag 'new_parent_type', such that the first node of a group
    has attribute 'start_criterion'==True and last node of a group has 
    'end_criterion'==True. Children that fall outside a group will be re-linked to
    old_parent to preserve document order.

    Applications: group tokens into phrases, letters into syllables etc.

    Note that start and end criteria must be provided by some upstream process --
    this function only carries out the restructuring.

    """
    
    ## sanity check: does element have the same number of "regroup_nodes_of_type" nodes before and
    ## after restructuring?  TODO: Make a more generic test of node integrity.
    initial_node_count = node.xpath("count(//%s)"%(regroup_nodes_of_type))
        
    collecting = False ## are we currently collecting items to be regrouped?
    
#     print
#     node.pretty_print()
#     print
    
    for child in node.xpath("./child::%s"%(regroup_nodes_of_type)):

        #child.pretty_print()

        ## Start a group if necessary:
        if child.get(start_criterion) == "True":   
            #print '---  start of phrase  --- '
            collecting = True
            group = Element(new_parent_type) ## start a group

        ## Do some thing with the node: ---------
        if collecting:
            #print '---  add to phrase group  --- '
            group.add_child(child)
        else:
            #print '---  node not in phrase --- '
            ## remove and reappend to preserve document order:
            node.remove(child)
            node.add_child(child)     

        ## End a group if necessary:
        if child.get(end_criterion) == "True":   
            #print '---  end of phrase  --- '             
            collecting = False
            node.add_child(group) ## add old group to utt

    ## sanity check concluded:
    final_node_count = node.xpath("count(//%s)"%(regroup_nodes_of_type))
#     print
#     node.pretty_print()
#     print 
    assert initial_node_count == final_node_count,"No. \
                nodes wrong after restructuring, %s -> %s"%(initial_node_count, final_node_count) 


def restructure_by_length(node, regroup_nodes_of_type="Letter", group_node_type="Morph", length_attr="length"):
    """
    Group a set of nodes under a group of specified node groups. The groups have a count defined that determines that maximum count of child nodes
    """
    regroup_nodes = iter(node.xpath("./child::%s"%regroup_nodes_of_type))

    try:
        for group_node in node.xpath("./child::%s"%group_node_type):
            for i in range(int(group_node.get(length_attr))):
                letter_node = next(regroup_nodes)
                node.remove(letter_node)
                group_node.add_child(letter_node)
    except StopIteration:
        pass

def add_predicted_silences(node):
    """
    If node has attribute silence_predicted and silence_predicted == "True",
    add child letter Letter with attribute modelname="sil"
    """
    ##print "**add_predicted_silences**"
    if node.has_attribute("silence_predicted") and node.get("silence_predicted") == True:
        ##node.pretty_print()
        node.remove_children()
        if node.get("silence_predicted") == "True":
            node.add_child(Element("Letter", modelname="sil"))
        ##node.pretty_print()


def ensure_times_consistent(utt, node_type):

    nodes = utt.xpath('//' + node_type)
    for (first, second) in zip(nodes[:-1], nodes[1:]):
        if first.attrib['end'] != second.attrib['start']:
            first.set('end', second.attrib['start'])

    return utt
