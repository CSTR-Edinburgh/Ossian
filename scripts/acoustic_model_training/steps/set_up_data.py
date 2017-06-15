#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
  
import sys
import re
import os
import random

from argparse import ArgumentParser

## find location of util relative to current script:
loc = os.path.abspath(os.path.join( __file__, os.pardir, os.pardir, 'util') )
sys.path.append(loc)


from util import *

def main_work():

    #################################################

    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-labdir', required=True, help= "...")
    a.add_argument('-cmpdir', required=True, help= "...")
    a.add_argument('-bindir', required=True, help= "...")
    a.add_argument('-outdir', required=True, help= "...")

    a.add_argument('-subset', required=False, help= "e.g. 30minutes / 5examples (=> 5 of each monophone)")
    
    opts = a.parse_args()
    BIN=opts.bindir
    
    ## check and parse 'subset' if it has been passed:
    kind = 'all' ## take all data by default
    if opts.subset:
        if opts.subset=='all':
            pass
        else:
            if not re.search('(\d+)(minutes|examples)', opts.subset):
                sys.exit('bad value for subset option: "%s"'%(opts.subset))
            s = re.search('(\d+)(minutes|examples)', opts.subset)
            (quantity, kind) = s.groups()

    # ===============================================
    
    if not os.path.isdir(opts.outdir + '/data/'):
        os.makedirs(opts.outdir + '/data/')


    cmplist = os.path.join(opts.outdir, 'data', 'uttlist.cmp')
    lablist = os.path.join(opts.outdir, 'data', 'uttlist.lab')
    monolist = os.path.join(opts.outdir, 'data', 'modellist.mono')
    fulllist = os.path.join(opts.outdir, 'data', 'modellist.full')
    monomlf = os.path.join(opts.outdir, 'data', 'mlf.mono')
    fullmlf = os.path.join(opts.outdir, 'data', 'mlf.full')
    
    
    ## 1) Make lists of .cmp and .lab (acoustic and linguistic feature) files:
    lab_ext = os.listdir(opts.labdir)[0].split('.')[-1] ## fragile...
    lab_ext = lab_ext.strip('~')  ## makes it a little less fragile
    cmp = [re.sub('\.cmp\Z', '', fname) for fname in os.listdir(opts.cmpdir) \
                                                            if fname.endswith('.cmp')]
    lab = [re.sub('\.'+lab_ext+'\Z', '', fname) for fname in os.listdir(opts.labdir) ]
    intersect = [name for name in lab if name in cmp] ## only where both are present
    if intersect == []:
        sys.exit('set_up_data.py: No matching data files found in %s and %s'%( \
                                                opts.labdir, opts.cmpdir))
    
    if kind=='minutes':
        mapping = get_duration_dict(intersect, opts.labdir, lab_ext)
        sec_needed = 60 * int(quantity)
        total = 0.0
        uttlist = mapping.keys()
        random.seed(1234567890)
        random.shuffle(uttlist)
        keeplist = []
        for utt in uttlist:
            total += mapping[utt]
            keeplist.append(utt)
            if total >= sec_needed:
                break
        print 'Keep %s of %s utts -- %s minutes'%(len(keeplist), len(uttlist), (total/60.0))
            
    elif kind=='examples':
        (mapping, found) = get_phone_dict(intersect, opts.labdir, lab_ext)
        full = False
        uttlist = mapping.keys()
        random.seed(1234567890)
        random.shuffle(uttlist)
        keeplist = []

        for utt in uttlist:
            for phone in mapping[utt]:
                found[phone] += 1
            keeplist.append(utt)
            full = True
            for value in found.values():
                if value < int(quantity):
                    full = False
            if full:
                break
        print 'Keep %s of %s utts '%(len(keeplist), len(uttlist))
        print 'Coverage: %s'%(found)

    else:
        assert kind=='all','Bad value for kind: %s -- something gone wrong.'%(kind)
        keeplist = intersect

    random.seed(56789)
    random.shuffle(keeplist)
    
    cmp = [os.path.join(opts.cmpdir, name + '.cmp') for name in keeplist]
    lab = [os.path.join(opts.labdir, name + '.' + lab_ext) for name in keeplist]

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


def get_duration_dict(uttlist, labdir, lab_ext):
    mapping = {}
    for base in uttlist:
        lab = os.path.join(labdir, base + '.' + lab_ext)
        last_line = readlist(lab)[-1]
        (start, end, phone) = re.split('\s+', last_line)
        mapping[base] = htk_to_sec(int(end))
    return mapping
    
def get_phone_dict(uttlist, labdir, lab_ext):
    mapping = {}   ## utt -> [a, b, c, b, ...]
    for base in uttlist:
        lab = os.path.join(labdir, base + '.' + lab_ext)
        lines = ''.join(readlist(lab))
        phones = re.findall('\-[^\+]+\+', lines)
        phones = [phone.strip('+-') for phone in phones]
        mapping[base] = phones

    all_phones = {}
    for phones in mapping.values():
         all_phones.update(dict(zip(phones,phones)))
    empty = dict(zip(all_phones.keys(), [0]*len(all_phones)))
    return mapping, empty    

    
if __name__=="__main__":

    main_work()

