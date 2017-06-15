#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Antti Suni - Antti.Suni@helsinki.fi
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
  
import sys
import re
import os

import default.fnames as fname
import default.const as const


from main.Voice import *
#import processors.GenericProcessor
import processors.UtteranceProcessor
import main.Corpus as Corpus
import util.Environment
from argparse import ArgumentParser
import logging
logging.basicConfig()  ##level=logging.DEBUG


def main_work():

    #################################################

    # root is one level below this file in directory structure, ie. below the 'scripts' folder
    ROOT = os.path.split(os.path.realpath(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))))[0]+'/'
    
    ## OSW: better to use      __file__     instead of:    inspect.getfile(inspect.currentframe())     in above line  ??



    dirs = {
        'ROOT': ROOT,
        'CONFIG': ROOT + "recipes/",
        'RULES': ROOT + "rules/",
        'VOICES': ROOT + "voices/",
        'TRAIN': ROOT + "train/",
        'CORPUS': ROOT + "corpus/",
        'BIN': ROOT + "/tools/bin/"

    }
        
    
    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-s', dest='speaker', required=True, \
                    help= "the name of the speaker: <ROOT>/corpus/<LANG>/<SPEAKER>")
    a.add_argument('-l', dest='lang', required=True, \
                    help= "the language of the speaker: <ROOT>/corpus/<LANG>")
    a.add_argument('-t', dest='stage', required=False, default="train",\
                    help=""" defines the current usage stage 
                        (definitions of stages should by found in <config>/recipe.cfg""")
    a.add_argument('-c', dest='clear', action='store_true', \
                    help= "clear any previous training data first")
    a.add_argument('-profile', dest='profile_code_performance', action='store_true')                    
    a.add_argument('-text', dest="text_corpus_name", default=False, \
                    help="""name of text corpus to be used for tool training, 
                            uses only voice prompts if not specified""")
    a.add_argument('-d', dest='command_line_corpus', required=False, action="append", \
                    help= "directories in arbitrary location containing training data")
    
    a.add_argument('-p', dest='max_cores', required=False, help="maximum number of CPU cores to use in parallel")
    a.add_argument('-bin', dest='custom_bindir') 
    a.add_argument('config', help="""configuration to use: naive, semi-naive,  gold,  
                            as defined in <ROOT>/recipes/<config> -directory""")
    opts = a.parse_args()

    if opts.custom_bindir != None:
        dirs['BIN'] = opts.custom_bindir 
        

    # ANT todo: maybe handle all the dirs stuff in Resources
    #
    if opts.profile_code_performance:
        train_with_profiling(opts, dirs)
    else:
        train(opts, dirs)


def train(opts, dirs):
    
    ## Handle corpus:
    print " -- Gather corpus"

    ## Get names of directories containing corpus data (all txt and wav):
    corpora = []    

    if opts.command_line_corpus:
        for location in opts.command_line_corpus:
            assert os.path.isdir(location)
            corpora.append(location)

    else:
        corpora.append(os.path.join(dirs['CORPUS'],opts.lang,fname.SPEAKERS, opts.speaker, "txt"))
        corpora.append(os.path.join(dirs['CORPUS'],opts.lang,fname.SPEAKERS, opts.speaker, "wav"))

        # additional large text corpus:
        if opts.text_corpus_name:
            corpora.append(os.path.join(dirs['CORPUS'], opts.lang,fname.TEXT_CORPORA, opts.text_corpus_name))



    ## Get names of individual txt and wav files:
    voice_data = []
    for c in corpora:
        for f in os.listdir(c):
            voice_data.append(os.path.join(c, f))

    corpus = Corpus.Corpus(voice_data)
    
    print " -- Train voice"
    voice = Voice(opts.speaker, opts.lang, opts.config, opts.stage, \
                dirs, clear_old_data=opts.clear, max_cores=opts.max_cores)

    ## Train the voice (i.e. train processors in pipeline context):       
    voice.train(corpus)



def train_with_profiling(opts, dirs):

    import cProfile, pstats, StringIO
    cProfile.runctx('train(opts, dirs)', \
                    {'train': train, 'opts': opts, 'dirs': dirs}, 
                    {}, 'mainstats')

    # create a stream for the profiler to write to
    profiling_output = StringIO.StringIO()
    p = pstats.Stats('mainstats', stream=profiling_output)

    # print stats to that stream
    # here we just report the top 30 functions, sorted by total amount of time spent in each
    p.strip_dirs().sort_stats('cumulative').print_stats(30)

    # print the result to the log
    print('---Profiling result follows---\n%s' %  profiling_output.getvalue() )
    profiling_output.close()
    print('---End of profiling result---')

if __name__=="__main__":

    main_work()
