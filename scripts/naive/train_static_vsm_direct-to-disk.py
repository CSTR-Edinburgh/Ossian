#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi


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

    get_schutze_01_cooc_matrix_gensim_direct_to_disk(text,feature_words,target_words,stored_model + ".MM")



    ## ------------------------------------------------
    ## 3) COMPUTE TRANSFORM, IMPOSE IT ON TRAINING DATA
    ## ------------------------------------------------

    print "Reading C cooc corpus..."

    C = corpora.MmCorpus(stored_model + ".MM")

    print 'Corpus C read:'
    print C
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



    ## clean up:
    os.remove(stored_model + ".MM")

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

def get_schutze_01_cooc_matrix_gensim_direct_to_disk(words,feature_words,target_words,file_out):

    """
    This function makes a co-occurrence matrix in Matrix Market format from a (possibly large)
    text corpus. The corpus is compiled direct to hard disk because for larger corpora (10 million words +)
    co-occurrence matrices typically don't fit in RAM. Recipe:

    1) Initialise matrix binary file on hard disk which can be randomly accessed.
    2) Pass through corpus, gather counts to the matrix binary file of left and right neighbours in feature_words
    3) Rewrite the counts gathered in binary matrix to a Matrix Market sparse matrix format file.
    4) Remove the matrix binary file.

    This is a very roundabout way of making co-occurrence matrices for smaller corpora, but it will
    be used everywhere for consistency.

    NOTE ON DUMMY COLUMN:
    Gensim doesn't like docs empty of contexts, nor does it accept placeholder (0,0) entries.
    Therefore, add an extra column of non-zero entries (1s). (Probably if there are lots of all-zero
    rows, different parameter settings are needed to make richer contexts...)
    """

    print "initialise random access matrix"

    ## 1) write to binary matrix format, random access: Init. the matrix file:
    import struct
    n_entries =  len(target_words) * (len(feature_words) * 2)
    entry_format = "1l" ## 1 4-byte integer per matrix cell

    ## init the matrix with zeros:
    f = open(file_out + '.ra_matrix', "w")
    for entry in xrange(n_entries):
        entry = 0 ## init matrix with all 0s
        packed_entry = struct.pack(entry_format, entry)
        f.write(packed_entry)
    f.close()

    ## open matrix file for random access:
    f = open(file_out + '.ra_matrix', 'r+b' )
    entry_size = struct.calcsize(entry_format)

    ## Define 2 functions for updating and accessing the matrix:
    def increment_record(f, row, col, entry_size, entry_format, rowlength):
        """
        Add one to specified element of the on-disk matrix
        """
        record_number = (row * rowlength) + col  ## from coords to place in contig list
                         ## ^-- else problems with row 0!
        ## get record:
        f.seek(entry_size * record_number)
        buffer = f.read(entry_size)
        record = struct.unpack(entry_format, buffer)

        ## record returned is (0,)
        record=record[0]

        new_nonzero = 0
        if record==0:
            new_nonzero = 1

        ## modify record:
        record += 1

        ## write record back in place:
        buffer = struct.pack(entry_format, record)
        f.seek(entry_size * record_number)
        f.write(buffer)

        return new_nonzero ## return 1 if a new nonzero entry has been created, else return 0

    def retrieve_row(f, row, entry_size, entry_format, rowlength):
        """
        Get specified row from the on-disk matrix as a Python list
        """
        #record_number = ( max(row-1, 0)) * rowlength  ## from coords to place in contig list
        #                 ## ^-- else problems with row 0!
        record_number =  row * rowlength  ## from coords to place in contig list

        ## get line:
        f.seek(entry_size * record_number)
        buffer = f.read(entry_size * rowlength)

        line_format_string = entry_format * rowlength   ## "1l1l1l1l..."
        line = list(struct.unpack(line_format_string, buffer) )

        return line

    feature_words_dict = dict(zip(feature_words, range(len(feature_words))))
    target_words_dict  = dict(zip(target_words, range(len(target_words))))

    rowlength= len(feature_words_dict) * 2
    nrows=len(target_words_dict)
    nonz=0

    print "Pass through corpus..."

    for i in range(1, len(words)-1):

        if i%100000==0:
            print "%s tokens done... "%(i)

        left = words[i-1]
        centre = words[i]
        right =  words[i+1]

        row = target_words_dict[centre]

        if left in feature_words_dict:
            col=feature_words_dict[left]
            new_nonzero = increment_record(f, row, col, entry_size, entry_format, rowlength)
            nonz += new_nonzero

        if right in feature_words_dict:
            col=feature_words_dict[right]
            col += len(feature_words_dict)  ## offset for "right" side of cooc matrix
            new_nonzero = increment_record(f, row, col, entry_size, entry_format, rowlength)
            nonz += new_nonzero

    ##f.close()  ## <-- don't close, keep it open to read whole lines back out in the next step.

    ### Now rewrite binary matrix data into MM format file:
    f_final = open(file_out, 'w')

    ## write 2-line header first
    f_final.write('%%matrixmarket matrix coordinate real general\n')
    ## In next line, +1 is for extra dummy column -- see NOTE ON DUMMY COLUMN  in note at top of function:
    f_final.write('%s %s %s\n'%(nrows,rowlength+1,nonz))

    for line_num in range(nrows):

        if line_num%10000==0:
            print 'Written %s lines to final'%(line_num)

        ## get line from binary matrix
        data=retrieve_row(f, line_num, entry_size, entry_format, rowlength)

        ## The dummy count column (see note at top of function):
        data.append(1)

        ## switch from "all entries" format to sparse format:
        for (col,count) in enumerate(data):
            if count > 0:
                f_final.write('%s %s %s\n'%(line_num + 1, col + 1, count)) ## +1 because MM starts counting at 1
    f_final.close()
    f.close()

    ## clean up
    os.remove(file_out + '.ra_matrix')


def get_schutze_02_cooc_matrix_gensim_direct_to_disk(words,feature_words,target_words,file_out, file_out_2):

    ## This is based closely on get_schutze_01_cooc_matrix_gensim_direct_to_disk.
    ## Would be nice to merge.
    """
    This function makes a co-occurrence matrix in Matrix Market format from a (possibly large)
    text corpus. The corpus is compiled direct to hard disk because for larger corpora (10 million words +)
    co-occurrence matrices typically don't fit in RAM. Recipe:

    1) Initialise binary matrix on hard disk which can be randomly accessed.
    2) Pass through corpus, gather counts to the binary matrix of left and right neighbours in feature_words
    3) Rewrite the counts gathered in binary matrix to a Matrix Market sparse matrix format file.
    4) Remove the binary matrix.

    This is a very roundabout way of making co-occurrence matrices for smaller corpora, but it will
    be used everywhere for consistency.

    NOTE ON DUMMY COLUMN:
    Gensim doesn't like docs empty of contexts, nor does it accept placeholder (0,0) entries.
    Therefore, add an extra column of non-zero entries (1s). (Probably if there are lots of all-zero
    rows, different parameter settings are needed to make richer contexts...)
    """

    #print "initialise random access matrix"

    ## 1) write to binary matrix format, random access: Init. the matrix file:
    import struct
    n_entries =  len(target_words) * (len(feature_words) * 2)
    entry_format = "1l" ## 1 4-byte integer per matrix cell

    ## init the matrix with zeros:
    f = open(file_out + '.ra_matrix', "w")
    for entry in xrange(n_entries):
        entry = 0 ## init matrix with all 0s
        packed_entry = struct.pack(entry_format, entry)
        f.write(packed_entry)
    f.close()

    ## open matrix file for random access:
    f = open(file_out + '.ra_matrix', 'r+b' )
    entry_size = struct.calcsize(entry_format)

    ## Define 2 functions for updating and accessing the matrix:
    def increment_record(f, row, col, entry_size, entry_format, rowlength):
        """
        Add one to specified element of the on-disk matrix
        """
        record_number = (row * rowlength) + col  ## from coords to place in contig list
                         ## ^-- else problems with row 0!
        ## get record:
        f.seek(entry_size * record_number)
        buffer = f.read(entry_size)
        record = struct.unpack(entry_format, buffer)

        ## record returned is (0,)
        record=record[0]

        new_nonzero = 0
        if record==0:
            new_nonzero = 1

        ## modify record:
        record += 1

        ## write record back in place:
        buffer = struct.pack(entry_format, record)
        f.seek(entry_size * record_number)
        f.write(buffer)

        return new_nonzero ## return 1 if a new nonzero entry has been created, else return 0

    def retrieve_row(f, row, entry_size, entry_format, rowlength):
        """
        Get specified row from the on-disk matrix as a Python list
        """
        #record_number = ( max(row-1, 0)) * rowlength  ## from coords to place in contig list
        #                 ## ^-- else problems with row 0!
        record_number =  row * rowlength  ## from coords to place in contig list

        ## get line:
        f.seek(entry_size * record_number)
        buffer = f.read(entry_size * rowlength)

        line_format_string = entry_format * rowlength   ## "1l1l1l1l..."
        line = list(struct.unpack(line_format_string, buffer) )

        return line

    feature_words_dict = dict(zip(feature_words, range(len(feature_words))))
    target_words_dict  = dict(zip(target_words, range(len(target_words))))

    rowlength= len(feature_words_dict) * 2
    nrows=len(target_words_dict)
    nonz=0

    #print "Pass through corpus #1..."  ## osw02 -- #1 added

    for i in range(1, len(words)-1):

        if i%100000==0:
            print "%s words done"%(i)

        left = words[i-1]
        centre = words[i]
        right =  words[i+1]

        row = target_words_dict[centre]

        if left in feature_words_dict:
            col=feature_words_dict[left]
            new_nonzero = increment_record(f, row, col, entry_size, entry_format, rowlength)
            nonz += new_nonzero

        if right in feature_words_dict:
            col=feature_words_dict[right]
            col += len(feature_words_dict)  ## offset for "right" side of cooc matrix
            new_nonzero = increment_record(f, row, col, entry_size, entry_format, rowlength)
            nonz += new_nonzero

    ##f.close()  ## <-- don't close, keep it open to read whole lines back out in the next step.


    """
    ### Now rewrite binary matrix data into MM format file:
    f_final = open(file_out, 'w')
            if impose_unitlength:
                    line=unitlength_list(line)
            if append_mean_vector:
                    float_line = [float(x) for x in line]
                    sum_line = [summed+new_val  for (summed, new_val) in zip(sum_line, float_line)]
            line=" ".join(line) + "\n"
            f.write(line)
    if append_mean_vector:
            sum_line = [summed / float(document_number)  for summed in sum_line]
            sum_line =   " ".join([str(x) for x in sum_line]) + "\n"
            f.write(sum_line)
    """

    ### Now rewrite binary matrix data into MM format file:
    f_final = open(file_out, 'w')

    for line_num in range(nrows):

        if line_num%10000==0:
            print 'Written %s lines to final'%(line_num)

        ## get line from binary matrix
        data=retrieve_row(f, line_num, entry_size, entry_format, rowlength)

        ## The dummy count column (see note at top of function):
        ##data.append(1)    ## REMOVED HERE FOR SCHUTZE 2  OSW2

        ## switch from "all entries" format to sparse format:
        for (col,count) in enumerate(data):
            if count > 0:
                f_final.write('%s %s %s\n'%(line_num + 1, col + 1, count)) ## +1 because MM starts counting at 1
    f_final.close()


    ## write 2-line header first
    f_final.write('%%matrixmarket matrix coordinate real general\n')
    ## In next line, +1 is for extra dummy column -- see NOTE ON DUMMY COLUMN  in note at top of function:
    ## REMOVED HERE FOR SCHUTZE 2  OSW2
    f_final.write('%s %s %s\n'%(nrows,rowlength,nonz))

    for line_num in range(nrows):

        if line_num%10000==0:
            print 'Written %s lines to final'%(line_num)

        ## get line from binary matrix
        data=retrieve_row(f, line_num, entry_size, entry_format, rowlength)

        ## The dummy count column (see note at top of function):
        ##data.append(1)    ## REMOVED HERE FOR SCHUTZE 2  OSW2

        ## switch from "all entries" format to sparse format:
        for (col,count) in enumerate(data):
            if count > 0:
                f_final.write('%s %s %s\n'%(line_num + 1, col + 1, count)) ## +1 because MM starts counting at 1
    f_final.close()

    f_final_final = open(file_out_2, 'w')
    #print "Pass through corpus #2..."  ## osw02 -- #2 added -- THIS PASS IS ALL NEW

    context_length = len(feature_words_dict)
    rowlength = context_length * 2
    nrows = len(target_words_dict)
    nonz = 0

    for i in range(1, len(words)-1):

        if i%100000==0:
            print "%s words done"%(i)

        left_ix   = target_words_dict[words[i-1]]
        centre_ix = target_words_dict[words[i]]
        right_ix  = target_words_dict[words[i+1]]

        ## Get the 4 relevant count vectors:
        right_of_left   = retrieve_row(f, left_ix,   entry_size, entry_format, rowlength)[context_length:]
        left_of_centre  = retrieve_row(f, centre_ix, entry_size, entry_format, rowlength)[:context_length]
        right_of_centre = retrieve_row(f, centre_ix, entry_size, entry_format, rowlength)[context_length:]
        left_of_right   = retrieve_row(f, right_ix,  entry_size, entry_format, rowlength)[:context_length]

        whole_row = right_of_left + left_of_centre + right_of_centre + left_of_right

    f_final_final.close()
    f.close()





    ## clean up
    os.remove(file_out + '.ra_matrix')



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



