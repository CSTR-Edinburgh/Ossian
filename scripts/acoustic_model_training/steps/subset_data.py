#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
  
import sys
import re
import os

from argparse import ArgumentParser

## find location of util relative to current script:
loc = os.path.abspath(os.path.join( __file__, os.pardir, os.pardir, 'util') )
sys.path.append(loc)

'''
Choose subset of data randomly -- either x minutes or at least x or each monophone.
'''
from util import *

def main_work():

    #################################################

    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-indir', required=True, help= "...")
    a.add_argument('-outdir', required=True, help= "...")
    a.add_argument('-bindir', required=True, help= "...")
    a.add_argument('-choose', required=True, help= "e.g. 30minutes / 5examples (=> 5 of each monophone)")
    
    opts = a.parse_args()
    BIN=opts.bindir
    
    ## parse 'choose':
    if not re.search('(\d+)(minutes|examples)', opts.choose):
        sys.exit('bad value for "choose" option')
    
    s = re.search('(\d+)(min|examples)', opts.choose)
    #(quantity, kind) = s.groups
    print s.groups() # (quantity, kind) 
    sys.exit('www')
    # ===============================================
    
    if not os.path.isdir(opts.outdir + '/data/'):
        os.makedirs(opts.outdir + '/data/')

    ## find 

    cmplist = os.path.join(opts.outdir, 'data', 'uttlist.cmp')
    lablist = os.path.join(opts.outdir, 'data', 'uttlist.lab')
    monolist = os.path.join(opts.outdir, 'data', 'modellist.mono')
    fulllist = os.path.join(opts.outdir, 'data', 'modellist.full')
    monomlf = os.path.join(opts.outdir, 'data', 'mlf.mono')
    fullmlf = os.path.join(opts.outdir, 'data', 'mlf.full')
    
    
    ## 1) Make lists of .cmp and .lab (acoustic and linguistic feature) files:
    lab_ext = os.listdir(opts.labdir)[0].split('.')[-1]
    cmp = [re.sub('\.cmp\Z', '', fname) for fname in os.listdir(opts.cmpdir) \
                                                            if fname.endswith('.cmp')]
    lab = [re.sub('\.'+lab_ext+'\Z', '', fname) for fname in os.listdir(opts.labdir) ]
    intersect = [name for name in lab if name in cmp] ## only where both are present
    if intersect == []:
        sys.exit('set_up_data.py: No matching data files found in %s and %s'%( \
                                                opts.labdir, opts.cmpdir))
    cmp = [os.path.join(opts.cmpdir, name + '.cmp') for name in intersect]
    lab = [os.path.join(opts.labdir, name + '.' + lab_ext) for name in intersect]
    writelist(cmp, cmplist)
    writelist(lab, lablist)
    
    
    ## 2) Make mlfs and model lists for monophones and fullcontext phones:
    comm=BIN+"""/HLEd -A -D -T 1 -V -l '*' -n %s -i %s -S %s %s
                """%(fulllist, fullmlf, lablist, nullhed(opts.outdir))
    print comm
    os.system(comm)
    
    comm=BIN+"""/HLEd -A -D -T 1 -V -l '*' -n %s -i %s -S %s -m %s %s
                """%(monolist, monomlf, lablist, nullhed(opts.outdir), fullmlf)
    print comm
    os.system(comm)
    

if __name__=="__main__":

    main_work()

