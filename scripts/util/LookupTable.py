#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

from naive.naive_util import *

class LookupTable(object):

### osw jan2012: No longer subclass of ConfiguredComponent -- stricter
##  interface -- just read data from table, assumed already made:

## osw aug 2014: is_phoneset added not to ask for MEAN etc in phoneset, and to strip comments.
## This could be made more general.

    def __init__(self, table_file, is_phoneset=False):

        self.table = {}  
        self.is_phoneset = is_phoneset

        assert os.path.isfile(table_file),"Table file %s does not exist"%(table_file)
        self.populate_table_from_file(table_file)
        self.verify_table()


    def verify_table(self):

        ## take keys of some arbitrary entry as fields names
        self.fields = sorted(self.table.values()[0].keys())

        ## check all entries have same fields
        for (k, v) in self.table.items():
            assert sorted(v.keys()) == self.fields

        if not self.is_phoneset:
            ## check for special entries:
            assert "_MEAN_" in self.table
            self.padding_lemma = "_MEAN_"
            if "_UNSEEN_" in self.table:
                self.unseen_lemma = "_UNSEEN_"
            else:
                self.unseen_lemma = "_MEAN_"
        else:
            assert "_UNSEEN_" in self.table
            self.unseen_lemma = "_UNSEEN_"

    def populate_table_from_file(self, fname):
        data = readlist(fname)
        
        if self.is_phoneset:
            ## remove scheme and python style comments:
            data = [line.split(';')[0] for line in data]
            data = [line.split('#')[0] for line in data]
            data = [line.strip(' \n') for line in data] # strip space:
            data = [line for line in data if line != ''] # remove empties
            
        data = [re.split("\s+", line) for line in data]

        ndim = len(data[0]) - 1  ## -1 accounts for lemma in col 1
        
        if self.is_phoneset: ## then treat first line as header
            header = data[0][1:]
            data = data[1:]
        else:    
            header = ["dim_%s"%(i+1) for i in range(ndim)] ## +1 to start at dim 1 not 0

        for (i, line) in enumerate(data):
            if len(line) != len(data[0]):
                if self.is_phoneset:
                    sys.exit('Wrong number of elements in phoneset line: ' + str(line))
                print 'Skip line %s -- wrong number of elements'%(i)  
                        ## just throw this representation away --
                        ## don't throw an error as previously
            else:
                lemma = line[0]
                
                self.table[lemma] = {}
                for (key, value) in zip(header, line[1:]):
                    self.table[lemma][key] = value

    def lookup(self, lemma, field=None):        
        assert field in self.fields,"LookupTable has no field '%s' among its fields: %s"%(field, " ".join(self.fields))
        return self.table.get(lemma, self.table[self.unseen_lemma])[field]  ## 2nd arg is default value
    
    def get_padding_value(self, field=None):
        assert field in self.fields,"LookupTable has no field '%s' among its fields: %s"%(field, " ".join(self.fields))
        return self.table[self.padding_lemma][field] 


    def has_entry(self, key):
        return (key in self.table)
