#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - October 2014 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk

## This is a lightweight replacement for the script previously with this name and now
## called train_static_vsm_gensim.py. It is more easily broken by large corpora, but is
## fine for several millions of words and settings of w and rank in the range we generally
## use.
##
## Differences include:
## -- sklearn's or numpy's SVD used instead of Gensim's incremental SVD
## -- only unseen method called B (absolute count threshold) supported
## -- removed usewords option -- always use the whole corpus
## -- read_text_corpus rewritten as generator read_text_corpus_to_triplets
## -- handle lines independently with padding_token
## -- option to normalise left and right count vectors

import sys
import os
import codecs
from argparse import ArgumentParser
import numpy
from numpy.linalg import svd as numpy_svd

from sklearn.decomposition import TruncatedSVD


## A couple of constants:
global padding_token, unseen_token, mean_token
padding_token = u'_END_'
unseen_token = u'_UNSEEN_'
mean_token = u'_MEAN_'


def main_work():

    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-corpus', required=True, help= "UTF-8 text file with space-delimited tokens")
    a.add_argument('-output', required=True, help= "A text file of output features")
    a.add_argument('-w', required=True, default="train", type=int, \
                            help="Number of feature words to use as context")
    a.add_argument('-rank', required=True, type=int, \
                            help= "Number of dimensions of transformed space")
    a.add_argument('-unseen', required=True, type=int, \
                            help="Tokens with count <= unseen are used to build an _UNSEEN_ model")
    a.add_argument('-svd', default='randomized',  \
                            help="SVD algorithm to use: randomized, arpack or exact")
    a.add_argument('-norm_counts', default=False, action='store_true',  \
                            help="Normalise left and right cooc vectors")
    a.add_argument('-no_mean', dest='append_mean_vector', default=True, action='store_false',  \
                            help="Suppress appending of mean vector")
                            
    opts = a.parse_args()
    
    train_static_vsm(opts.corpus, opts.output, opts.w, opts.rank, opts.unseen, opts.svd, \
                                opts.norm_counts, append_mean_vector=opts.append_mean_vector)
    # ================================================

def read_text_corpus_to_triplets(fname, nwords=float('inf')):
    with codecs.open(fname, 'r', encoding='utf-8') as f: 
        for line in f.xreadlines():
            line = line.strip("\n ")
            line = line.split(" ")
            for triplet in zip([padding_token] + line[:-1], line, line[1:] + [padding_token]):
                yield triplet
                
                
def train_static_vsm(textfile_in, stored_model, w, rank, unseen_threshold, svd_type, \
                                                    norm_counts, append_mean_vector=True):

    assert unseen_threshold > 0,'Unseen method A no longer supported'

    ## ------------------------------------------------
    ## 0) CHECK OUTPUT LOCATION
    ## ------------------------------------------------

    ## Check we will be able to make output where specified:
    working,tail = os.path.split(stored_model)
    if not os.path.isdir(working):
        sys.exit('Path %s does not exist'%(working))

    ## ------------------------------------------------
    ## 1) FIRST PASS -- COUNTING
    ## ------------------------------------------------

    print 'Count types...'

    ## get target words, sorted by descending frequency
    ## count wordtypes:
    counts={}
    for (left_neighbour,word,right_neighbour) in read_text_corpus_to_triplets(textfile_in):
        if word not in counts:
            counts[word] = 0
        counts[word] += 1

    ## sort by freq:
    count_list = [(count,word) for (word,count) in counts.items()]
    count_list.sort()
    count_list.reverse()
    
    ## get the first w words we'll count coocurrances for ('feature words' in Biemann)
    if len(count_list) < w:
        w = len(count_list)
    feature_words = [word for (count, word) in count_list[:w-2]] + [padding_token, unseen_token]
    target_words = [unseen_token] + [word for (count, word) in count_list if count > unseen_threshold] 

    ## Always count cooc with padding_token, but never use it as target word:
    counts[padding_token] = unseen_threshold + 1

    ## ------------------------------------------------
    ## 2) SECOND PASS -- MAKE COOCC. MATRIX C
    ## ------------------------------------------------

    print 'Assemble cooccurance matrix...'
    
    n = len(feature_words)
    m = len(target_words)
    C = numpy.zeros((m, n*2))

    ## make maps from surface forms of token to indexes:
    left_feature_words_dict = dict(zip(feature_words, range(len(feature_words))))
    right_feature_words_dict  = dict(zip(feature_words, [val + len(feature_words) \
                                                for val in range(len(feature_words))] ))
    target_words_dict  = dict(zip(target_words, range(len(target_words))))

    #print target_words_dict
    for (left,centre,right) in read_text_corpus_to_triplets(textfile_in):
        
        ## Handle unseen token rewriting:
        if counts[centre] <= unseen_threshold:
            centre = unseen_token
        if counts[left] <= unseen_threshold:
            left = unseen_token
        if counts[right] <= unseen_threshold:
            right = unseen_token    
                    
        if left in left_feature_words_dict:
            C[target_words_dict[centre], left_feature_words_dict[left]] += 1
        if right in right_feature_words_dict:
            C[target_words_dict[centre], right_feature_words_dict[right]] += 1
    
    
    if norm_counts:
        
        ## threshold to avoid divide by zero errors (-> NaNs):
         
        left_sums = numpy.sum(C[:, :n], axis=1).reshape(m,1)
        left_sums[left_sums < 1.0] = 1.0 ## use mask to threshold
        C[:, :n] /= left_sums
        
        right_sums = numpy.sum(C[:, n:], axis=1).reshape(m,1)
        right_sums[right_sums < 1.0] = 1.0 ## use mask to threshold
        C[:, n:] /= right_sums
        
        # tots = numpy.sum(C, axis=1)
        
        
    ## ------------------------------------------------
    ## 3) FACTORISATION
    ## ------------------------------------------------
    
    print 'Factorise cooccurance matrix...'

    if svd_type == 'exact':
        U,D,V = numpy_svd(C, full_matrices=False)
        D = numpy.diag(D[:rank])
        transformed_C = numpy.dot(U[:,:rank], D)
    
    elif svd_type in ['randomized', 'arpack']:
        svd = TruncatedSVD(n_components=rank, algorithm='randomized', random_state=999) 
        svd.fit(C)
        transformed_C = svd.transform(C) 
        '''
        ## reconstruction -- singular values seem to be multiplied into U or V:
        rec = numpy.dot(transformed_C, svd.components_)
        print rec[:3, :]
        print C[:3, :]
        '''
        
    else:
        sys.exit('Unknown SVD type: %s'%(svd_type))
    
    if append_mean_vector:
        mean_vec = numpy.mean(transformed_C, axis=0)
        transformed_C = numpy.vstack([transformed_C, mean_vec])
        target_words = target_words + [mean_token]
    
    ## ------------------------------------------------
    ## 4) WRITE OUTPUT:
    ## ------------------------------------------------
    stored_model += '.table'  ## TODO: historical -- clean this up. 
    print 'Write output to %s'%(stored_model)
    f = codecs.open(stored_model, 'w')
    for (lemma, feats) in zip(target_words, transformed_C):
        line =  [lemma] + [str(val) for val in feats]
        line = ' '.join(line) + '\n'
        f.write(line)
    f.close()    
        
        
if __name__=="__main__":

    main_work()
    
    
