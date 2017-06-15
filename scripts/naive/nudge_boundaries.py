#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi



'''

 When the input alignment
 for a segment shows it to be less than the minimum HTS duration 
 of 25 ms (5ms shift * 5 states = 25ms), it is ignored by HINIT, so 
 a "0 examples" error is raised and training stops. 

This is only an issue with small toy databases.

This script nudges phone boundaries as necessary to make sure that each monophone has at least
1 instance longer than minumum_duration (ms). This is only a temporary work-around.

'''

import sys
import os
import re


from naive_util import *

def main_work():

    #################################################

    # ======== Get stuff from command line ==========

    def usage():
        print "Usage: ......  "
        sys.exit(1)

    # e.g. 

    try:
        label_indir = sys.argv[1]
        label_outdir = sys.argv[2]
        mindur_ms = int(sys.argv[3])
    except:
        usage()


    if not os.path.isdir(label_outdir):
        os.makedirs(label_outdir)
    #################################################
    
    minimum_duration = ms_to_htk(mindur_ms)
    
    
    ## Get list of utterances for which utt files exist:
    lab_list = sorted(os.listdir(label_indir))   

    ## first pass -- find the problem segments     
    phones = {}
                 
    for labname in lab_list:
        #print labname
        #print " Apply voice method %s to utt %s"%(method_to_call, utt)
        lab = readlist(os.path.join(label_indir, labname))     

        #print lab
        lab = [re.split("[\s\-\+]+", line) for line in lab]
        assert len(lab) == sum([len(line)==4 for line in lab]) ## assert all lines are 4 long

       # lab = [(phone, int(end)-int(start))  for (start, end, phone, stuff) in lab]
        for (start, end, phone, stuff) in lab:

            length = int(end)-int(start)
            
            if phone not in phones:
                phones[phone] = 1  # 1 means a problem
            if length >= minimum_duration:    
                phones[phone] = 0  # 0 means no problem
                
    print phones
#    
    ## 2nd pass -- fix 1st instance of the problem segments     
    for labname in lab_list:

        ends = []
        #print " Apply voice method %s to utt %s"%(method_to_call, utt)
        lab = readlist(os.path.join(label_indir, labname))     

        lab = [re.split("[\s\-\+]+", line) for line in lab]
        assert len(lab) == sum([len(line)==4 for line in lab]) ## assert all lines are 4 long
        lab = [(phone, int(end), int(end)-int(start))  for (start, end, phone, stuff) in lab]
        for i in range(len(lab)-1):
            (phone, end, length) = lab[i]

            if phones[phone] == 1:                
                if length < minimum_duration:
                    diff = minimum_duration - length
                    (next_phone, _next_end, next_length) = lab[i+1]
                    if next_length >= diff:
                        end += diff                     
                        phones[phone] = 0  # 0 means no problem
            ends.append(end)


        ## remake label with new times:
        starts = [0] + ends[:-1]
        lab = readlist(os.path.join(label_indir, labname))   
        lab = [re.split("\s+", line) for line in lab]
        names = [name for (s,e,name) in lab]
        f = open(os.path.join(label_outdir, labname), "w")
        for (s,e,name) in zip(starts, ends, names):
            f.write("%s %s %s\n"%(s,e,name))
        f.close()            

#                    
#    ## 3rd pass -- checked all is fixed
             
    fixed_phones  = {}
    phone_to_labs = {} ## to track which utts each phone appears in

    for labname in lab_list:
        #print " Apply voice method %s to utt %s"%(method_to_call, utt)
        lab = readlist(os.path.join(label_outdir, labname))     

        lab = [re.split("[\s\-\+]+", line) for line in lab]
        assert len(lab) == sum([len(line)==4 for line in lab]) ## assert all lines are 4 long
       # lab = [(phone, int(end)-int(start))  for (start, end, phone, stuff) in lab]
        for (start, end, phone, stuff) in lab:

            length = int(end)-int(start)

            if phone not in phone_to_labs:
                phone_to_labs[phone] = []
            if labname not in  phone_to_labs[phone]:
                phone_to_labs[phone].append(labname)

            if phone not in fixed_phones:
                fixed_phones[phone] = 1  # 1 means a problem
            if length >= minimum_duration:    
                fixed_phones[phone] = 0  # 0 means no problem
                

    ## If all else has failed, we will just throw some utterances out to avoid bad phone lengths:                    
    if 1 in fixed_phones.values():
        bad_utts = []
        for (key,val) in fixed_phones.items():
                if val==1:
                    bad_utts.extend(phone_to_labs[key])
        bad_utts = dict(zip(bad_utts, bad_utts)).keys() ## unique it
        print 'Warning -- phone lengths are problematic: remove the bad utterances: %s'%(" ".join(bad_utts))
        for utt_name in bad_utts:
            os.remove(os.path.join(label_outdir, utt_name))
    else:
        print "phones fixed OK"



if __name__=="__main__": 

        main_work()


