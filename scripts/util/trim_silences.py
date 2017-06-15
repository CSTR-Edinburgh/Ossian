#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - April 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


## This script is meant to handle imperfect data, where there are extra words 
## at the ends of the transcript that are not present in the audio file. 
## It assumes that these extra words are aligned with the utterance-initial and 
## -final silences by the TASSAL aligner -- assuming this is correct, removing
## most of the silence from the ends of the wave files should fix the problem.



import sys
import re
import os
from glob import glob 

from argparse import ArgumentParser

from draw_hts_tree_simple import parse_treefile_general, treelist_to_dict, add_leaf_entries

## ~/my_python ./scripts/util/trim_silences.py  -inlab train/rm/speakers/SSW13/naive/lab/ -inwav corpus//rm/speakers/SSW13/wav/ -outlab train/rm/speakers/SSW13/naive/trim_lab/ -outwav train/rm/speakers/SSW13/naive/trim_wav/


def main_work():

    #################################################
    # ======== Get stuff from command line ==========

    a = ArgumentParser()

    a.add_argument('-inlab', required=True, help='labels output by the aligner')
    a.add_argument('-inwav', required=True, help='wave files to be trimmed')
    a.add_argument('-outlab', required=True, help='directory for new trimmed labels -- use these for training HTS models')
    a.add_argument('-outwav', required=True, help='directory for new trimmed wave files -- extract acoustic features from these to train HTS models')
    a.add_argument('-padding', type=int, default=150, help="Duration (ms) of silence to leave at utterance ends")
    
    opts = a.parse_args()

    #################################################

    for direc in [opts.outlab, opts.outwav]:
        if not os.path.isdir(direc):
            try:
                os.makedirs(direc)
            except:
                sys.exit("Cannot make output directory: %s"%(direc))

    #################################################
    padding = opts.padding * 10000  ## ms --> htk units

    #################################################

    for lab in glob(opts.inlab + "/*.lab"):

        base = os.path.basename(lab)
        print base
        label = readlab(lab)
        ## first and last sils:
        old_start = 0
        old_end = label[-1][1]

        #        new_start = old_start
        #        for (i, (start,end,model)) in enumerate(label):
        #            print i
        #            if "-sil+" not in model:
        #                break
        #            new_start = end


        #        new_end = old_end
        #        label.reverse()
        #        for (i, (start,end,model)) in enumerate(label):
        #            print i
        #            if "-sil+" not in model:
        #                break
        #            new_end = start

        ## Assume only single initial and final sils
        assert "-sil+" in label[0][2]
        assert "-sil+" in label[-1][2]
        #--
        new_start = label[0][1]
        new_end = label[-1][0]
        #--
        new_start -= padding
        new_end += padding
        #--
        new_start = max(old_start, new_start)
        new_end = min(new_end, old_end)

        ## 
        ## shift all labels along:
        starts = [line[0]-new_start for line in label]
        starts[0] = 0
        ends = [line[1]-new_start for line in label]
        ends[-1] = new_end - new_start
        models = [line[2] for line in label]

        outlines = []
        for (start, end, name) in zip(starts, ends, models):
            outlines.append("%s %s %s"%(start, end, name))

        writefile(outlines, os.path.join(opts.outlab, base))

        ## trim waveform accordingly:
        base = base.replace(".lab", ".wav")
        wav = os.path.join(opts.inwav, base)
        start_secs = new_start / 10000000.0
        dur_secs = (new_end - new_start) / 10000000.0
        trimwav = os.path.join(opts.outwav, base)
        comm = "sox %s %s trim %s %s"%(wav, trimwav, start_secs, dur_secs)
        os.system(comm)

def readlab(fname):
    lab = readfile(fname)
    lab = [re.split("\s+", line) for line in lab]
    lab = [(int(line[0]), int(line[1]), line[2]) for line in lab]
    return lab

def readfile(fname):
    f = open(fname, "r")
    data = f.readlines()
    f.close()
    data = [line.strip(" \n") for line in data]
    return data

def writefile(data, fname):
    f = open(fname, "w")
    f.write("\n".join(data) + "\n")
    f.close()




if __name__=="__main__":

    main_work()
