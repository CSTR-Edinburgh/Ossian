#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

## This is a faster version of what was train_static_vsm_direct-to-disk.py, and replaces it as
## train_static_vsm.py. 


#    Oliver Watts
#    Wed 19 Oct 2011
#    Script to call Gensim 0.5 to train Vector Space Models with SVD of words/letters/etc.
#    Call script with no arguments or look at usage for details.

#    Basically, this script builds a cooccurrance matrix and uses the "gensim" package
#    (old version 0.5.0: http://pypi.python.org/pypi/gensim/0.5.0) to do SVD.

#    Get the package and unpack it. You don't need to install using the scripts included --
#    just put environment variable GENSIM_LOC pointing to the ./gensim-0.5.0/src of the
#    package:

#    export GENSIM_LOC = <PATH-TO-PACKAGE>/gensim-0.5.0/src

#    There are some notes in the script about command line arguments.


import sys
import os
import pickle

from gensim import corpora, models

import numpy
from numpy import *
from numpy.linalg import norm

import shelve




def train_static_vsm(textfile_in, usewords, stored_model, w, rank, unseen_method):


    #################################################
    holdout_percent = 0.01  ## fraction of corpus to hold out for unseen method A
    #################################################


    ## ------------------------------------------------
    ## 0) CHECK LOCATIONS
    ## ------------------------------------------------

    ## Check we will be able to make output where specified:
    working,tail = os.path.split(stored_model)
    if not os.path.isdir(working):
        print 'Path %s does not exist'%(working)
        sys.exit(1)


    ## ------------------------------------------------
    ## 1) READ INPUT, REWRITE WORDS WITH _UNSEEN_ SYMBOL
    ## ------------------------------------------------

    ## get data from simple ascii file (sentence per line [ignored]),
    ## lowercased and tokenised if necessary

    text = read_text_corpus(textfile_in)

    if usewords > 0:
        text=text[:usewords]

    ## add label symbol
    if unseen_method == 0:
        text=add_unseen_symbol_method_A(text,holdout=holdout_percent)
    else:
        text=add_unseen_symbol_method_B(text,unseen_method)


    ## ------------------------------------------------
    ## 2) MAKE CO-OCCURRENCE MATRIX C
    ## ------------------------------------------------

    ## get target words, sorted by descending frequency
    ## count wordtypes:
    counts={}
    for word in text:
        if word not in counts:
            counts[word] = 0
        counts[word] += 1

    ## sort by freq:
    counts = [(count,word) for (word,count) in counts.items()]
    counts.sort()
    counts.reverse()
    
    ## get the first w words we'll count coocurrances for ('feature words' in Biemann)
    if len(counts) < w:
        w = len(counts)
    feature_words = [word for (count, word) in counts[:w]]
    target_words = [word for (count, word) in counts]

    C = get_schutze_01_cooc_matrix_gensim(text,feature_words,target_words)
#    get_schutze_01_cooc_matrix_gensim_direct_to_disk(text,feature_words,target_words,stored_model + ".MM")



    ## ------------------------------------------------
    ## 3) COMPUTE TRANSFORM, IMPOSE IT ON TRAINING DATA
    ## ------------------------------------------------

#    print "Reading C cooc corpus..."

#    C = corpora.MmCorpus(stored_model + ".MM")

    print 'Corpus C read:'
    #print C
    print

    print "Transform  C cooc corpus ..."
    lsi_C = models.LsiModel(C,  numTopics=rank)

    print "Transform C cooc data..."
    transformed_C = lsi_C[C]



    ## ------------------------------------------------
    ## 4) STORE VARIOUS OUTPUTS
    ## ------------------------------------------------


    ## impose unit length on the transformed training data and store:
    gensim_corpus_to_textfile(transformed_C, stored_model + ".table", impose_unitlength=True, append_mean_vector=True, write_lemma=target_words)


### SKIP THE FOLLOWING FOR NOW:
#    ## store un-reduced matrix
#    gensim_corpus_to_textfile(C, stored_model + ".dat", impose_unitlength=False, write_lemma=target_words)

#    ## store the transform itself
#    pickle_data(lsi_C, stored_model + ".model")

#    ## store as Python shelve database:
#    shelve_gensim_corpus(transformed_C, stored_model + ".shelved", target_words, impose_unitlength=True, append_mean_vector=True)



    
def read_text_corpus(fname):

    f=open(fname, "r")
    data=f.readlines()
    f.close()

    data=[line.strip("\n ") for line in data]
    data=[line.split(" ") for line in data]
    text=[]
    for line in data:
        text.extend(line)
    return text


def pickle_data(data, fname):
    f = open(fname, "w")
    pickle.dump(data, f)
    f.close()

def unpickle_data(fname):
    print '  *** unpickle_data *** '
    assert os.path.isfile(fname),'File %s doens\'t exist'%(fname)

    f=open(fname, "r")
    data = pickle.load(f)
    f.close()
    return data

def readlist(filename):
    f = open(filename, "r")
    data = f.readlines()
    f.close()
    data = [line.strip("\n") for line in data]
    return data

def writelist(data, filename):
    data=[str(x) for x in data]
    f = open(filename, "w")
    data = "\n".join(data)  +  "\n"
    f.write(data)
    f.close()

def array_to_textfile(array, filename):
    f = open(filename, "w")
    for row in array:
        row = row.tolist()
        row = row  # because now, we have a list of lists
        # turn list contents from floats to strings:
        row = [str(x) for x in row]                     #  NORMAL STRING CONVERSION
        row = " ".join(row)
        row = row + "\n"
        f.write(row)
    f.close()



def add_unseen_symbol_method_A(text,holdout=0.10):
    """
    A portion of the training corpus ("holdout": default 10%)
    is set aside while a list of seen types is compiled from the remainder of the corpus.
    The tokens of the heldout set absent from the rest of the corpus are rewritten _UNSEEN_.
    """
    devset_length=int(len(text)*float(holdout))
    print 'account for unseen tokens using %s words out of %s (%s)'%(devset_length,len(text),holdout)
    holdout=text[:devset_length]
    rest   =text[devset_length:]
    types={}
    for token in rest:
        types[token]=token

    ## count # types in whole text and holdout section (just for reporting):
    all_types = {}
    for token in text:
        all_types[token]=token

    ho_types = {}
    for token in holdout:
        ho_types[token]=token
    print "%s types in whole text of %s tokens"%(len(all_types), len(text))
    print "%s types in holdout section of %s tokens"%(len(ho_types), len(holdout))
    print "%s types in main section of %s tokens"%(len(types), len(rest))


    holdout=[types.get(word, '_UNSEEN_') for word in holdout]  ## rewrite
    rewritten= holdout + rest
    return rewritten



def add_unseen_symbol_method_B(text, threshold):
    """
    Rewrite words with count <= threshold as _UNSEEN_
    """
    counts={}
    for word in text:
        if word not in counts:
            counts[word] = 0
        counts[word] += 1

    for word in counts.keys():
        if counts[word] <= threshold:
            del counts[word]
    for word in counts.keys():
        counts[word] = word
    text=[counts.get(word, '_UNSEEN_') for word in text]  ## rewrite
    return text


def gensim_corpus_to_textfile(corpus, fname, impose_unitlength=True, append_mean_vector=False, write_lemma=False):
    """
    Write one line at a time
    
    If write_lemma is a list, check length is same as corpus length, then write 
    entry at start of each textfile line.
    """

    n = find_ncolumns_in_gensim_corpus(corpus)
    m = len(corpus)

    print '  *** gensim_corpus_to_textfile *** '
    print 'm: %s   n: %s'%(m,n)
    f=open(fname, "w")
    document_number=0

    if write_lemma:
        assert m==len(write_lemma),"Number of entries in corpus and lemma list do not match"

    if append_mean_vector:
        sum_line = [0.0] * n

    for (i, doc) in enumerate(corpus):
        line = ["0"] * n
        for (term_number, value) in doc:
            line[term_number] = str(value)
        document_number+=1
        if impose_unitlength:
            line=unitlength_list(line)
        if append_mean_vector:
            float_line = [float(x) for x in line]
            sum_line = [summed+new_val  for (summed, new_val) in zip(sum_line, float_line)]
        line=" ".join(line) + "\n"
        if write_lemma:
            line = write_lemma[i] + " " + line
        f.write(line)
    if append_mean_vector:
        sum_line = [summed / float(document_number)  for summed in sum_line]
        sum_line =   " ".join([str(x) for x in sum_line]) + "\n"
        if write_lemma:
            sum_line = "_MEAN_ " + sum_line
        f.write(sum_line)
    f.close()


def find_ncolumns_in_gensim_corpus(corpus):
    """
    find highest index to get appropriate n dimensionality of written matrix
    """
    indexes={}
    c=0
    for doc in corpus:
        if len(doc) > 0:
            highest_in_doc = max([ix for (ix, value) in doc])
            indexes[highest_in_doc] = 'dummy'
    n = max(indexes.keys()) + 1
    return n

def shelve_gensim_corpus(corpus, fname, lemma_list, impose_unitlength=True, append_mean_vector=False):
    """
    Keys are lemmas and _MEAN_ if append_mean_vector
    """
    assert len(lemma_list)==len(corpus)

    n = find_ncolumns_in_gensim_corpus(corpus)
    m = len(corpus)

    print '  *** shelve_gensim_corpus *** '
    print 'm: %s   n: %s'%(m,n)
    f = shelve.open(fname)
    document_number=0

    if append_mean_vector:
        sum_line = [0.0] * n

    for doc in corpus:
        line = ["0"] * n
        for (term_number, value) in doc:
            line[term_number] = str(value)   ### !!!!!!!! remove str???!!!!

        if impose_unitlength:
            line=unitlength_list(line)
        if append_mean_vector:
            float_line = [float(x) for x in line]
            sum_line = [summed+new_val  for (summed, new_val) in zip(sum_line, float_line)]

        f[lemma_list[document_number]] = line

        document_number+=1

    if append_mean_vector:
        sum_line = [summed / float(document_number)  for summed in sum_line]

        f["_MEAN_"] = sum_line
    f.close()


def unitlength_list(l):
    """
    strings  --> floats
    list --> array
    impose unit length
    array -> list
    ##floats --> strings -- NO -- return floats
    """
    l=[float(x) for x in l]
    vect=array(l)
    magnitude=norm(vect)
    vect /= magnitude   ## elementwise
    outlist=vect.tolist()
    outlist=[str(x) for x in outlist]
    return outlist

def rows_to_unit_length(A):
    """
    Currently unused  by this script...
    """
    m,n = shape(A)
    B=zeros((m,n))
    for row in range(m):
        vect=A[row,:]
        magnitude=norm(vect)
        vect /= magnitude   ## elementwise
        B[row,:] = vect[:]
    return B

    
def corpus_to_triplets(words):
    
    feats = [(words[i-1], words[i], words[i+1])  \
            for i in range(1, len(words)-1)]
    return feats    

def get_schutze_01_cooc_matrix_gensim(text,feature_words,target_words): # freqsorted_vocab,feat_sorted,n_freq_words):    

    C = get_schutze_01_cooc_matrix(text,feature_words,target_words)

    C = add_column_for_empty(C)

    corpus = array_to_gensim_corpus(C)
    return corpus

def get_schutze_01_cooc_matrix(words,feature_words,target_words): # freqsorted_vocab,feat_sorted,n_freq_words):    

    n = len(feature_words)
    
    m = len(target_words)
    
    C = zeros((m, n*2))

    left_feature_words_dict = dict(zip(feature_words, range(len(feature_words))))
    right_feature_words_dict  = dict(zip(feature_words, [val + len(feature_words) for val in range(len(feature_words))] ))
    target_words_dict  = dict(zip(target_words, range(len(target_words))))


    for i in range(1, len(words)-1):

        if i%100000==0:
            print "%s tokens done... "%(i)

        left = words[i-1]
        centre = words[i]
        right =  words[i+1]


        if left in left_feature_words_dict:
            C[target_words_dict[centre], left_feature_words_dict[left]] += 1
        if right in right_feature_words_dict:
            C[target_words_dict[centre], right_feature_words_dict[right]] += 1
    
    return C    

    
def add_column_for_empty(C):
    """
    Gensim doesn't like docs empty of contexts, nor does it accept placeholder (0,0) entries
    Therefore, add an extra row of non-zero entries (1s). (Probably if there are lots of all
    zero rows, different parameter settings are needed to make richer contexts...)
    """
    dim,n=shape(C)
    extracol=ones((dim,1))
    out=hstack((C,extracol))
    return out


def array_to_gensim_corpus(C):
    """
    Use terms "term" and "document" as in classic LSI rather than 
    truthfully for our application.
    """    
    corpus = []
    m,n = shape(C)
    print '  *** array_to_gensim_corpus *** '
    print 'm: %s   n: %s'%(m,n)
    for document in range(m):
        doc = []
        for term in range(n):
            if C[document,term] != 0.0:
                doc.append((term, C[document,term]))
        corpus.append(doc)
    return corpus    



if __name__=="__main__":

    #################################################

    # ======== Get stuff from command line ==========

    def usage():
        print "Script was called like:"
        print sys.argv
        print
        print "\n\n\n"
        print "Script to train continuous word/letter/etc. space models"
        print "Usage: train_vsm_type_1.py text_corpus usewords stored_model w rank unseen_method"
        print ""
        print "   where text_corpus  --   is a simple ascii text file (1 sentence per line [ignored]),"
        print "                           already lowercased / tokenised / etc. as required "
        print "          usewords     --  Take first usewords words of corpus -- 0 for whole corpus  "
        print "          stored_model --  stem for output files "
        print "         w             --  number of feature words to use as context"
        print "         rank          --  number of dimensions of transformed space to keep"
        print "         unseen_method --  method used for training model for unseen words:"
        print "                           * If 0 use method A:      A portion of the training corpus "
        print "                             ('holdout': default 10%) is set aside while a list of seen "
        print "                             types is compiled from the remainder of the corpus. The "
        print "                             tokens of the heldout set absent from the rest of the corpus "
        print "                             are rewritten _UNSEEN_."
        print "                           * If > 0: Rewrite words with count <= threshold as _UNSEEN_"
        print
        print " E.g.:"
        print "~/proj/whole_system/script/train_vsm_type_1.py ~/pr/distrib_pos/wsj.txt 5000 ~/pr/TEMP/vsm_wsj_test4 250 50 1"
        print ""
        print " _UNSEEN_ and _MEAN_ are added to vocab and features are made for them."
        print
        print "Outputs: "
        print
        print "<stored_model>.dat   ---   raw co-occurrance matrix as text file"
        print "<stored_model>.trans ---   transformed training data as text file"
        print "<stored_model>.lemma ---   vocab list matching *.trans line-for-line: _UNSEEN_ and _MEAN_ are added    "
        print "                          _MEAN_ not in *.dat -- *.dat 1 line shorter.     "
        print "<stored_model>.model ---   the pickled gensim model (for folding new stuff in instead "
        print "                           of using _UNSEEN_)  "
        print "\n\n\n"

        sys.exit(1)

    try:

        textfile_in  = sys.argv[1]  ##
        usewords    = int(sys.argv[2]) ## Take first n words of corpus -- 0 for all corpus.
        stored_model = sys.argv[3]     ## <stored_model>.dat
        w       = int(sys.argv[4])
        rank    = int(sys.argv[5])
        unseen_method    = int(sys.argv[6]) ## If 0 use method A (hold out holdout_percent * 100 % of corpus).
                                            ## If bigger, mark words with count <= unseen_method  as _UNSEEN_.


    except:
        usage()

    print [usewords]
    train_static_vsm(textfile_in, usewords, stored_model, w, rank, unseen_method)



