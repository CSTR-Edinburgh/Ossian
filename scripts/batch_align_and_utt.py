#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Antti Suni - Antti.Suni@helsinki.fi
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk

import sys
import re
import os
import fileinput

from main.Voice import *
#import processors.GenericProcessor
import processors.UtteranceProcessor
import default.fnames as fname

from argparse import ArgumentParser
from lxml import etree
import logging
logging.basicConfig()  ##level=logging.DEBUG

from naive.naive_util import readlist, get_basename

def main_work():

    #################################################

    # root is one level below this file in directory structure, ie. below the 'scripts' folder
    ROOT = os.path.split(os.path.realpath(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))))[0]+'/'
    
    dirs = {
        'ROOT': ROOT,
        'CONFIG': ROOT + "recipes/",
        'VOICES': ROOT + "voices/",
        'TRAIN': ROOT + "train/",
        'RULES': ROOT + "rules/",
        'CORPUS': ROOT + "corpus/",
        'BIN': ROOT + "/tools/bin/"
        }
    
    
    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-s', dest='speaker', required=True, \
                    help= "the name of the speaker: <ROOT>/corpus/<LANG>/<SPEAKER>")
    a.add_argument('-l', dest='lang', required=True, \
                    help= "the language of the speaker: <ROOT>/corpus/<LANG>")
    a.add_argument('-o', dest='output', required=False, default=False, \
                    help= "output audio here")
    a.add_argument('-w', dest='input_wav', required=False, default=False, \
                    help= "reference waves to compute alignment against")
    a.add_argument('-u', dest='output_utt', required=False, default=False, \
                    help= "output utt files here")
#    a.add_argument('-t', dest='stage', required=False, default="runtime_natural_duration", \
#                    help=""" defines the current usage stage 
#                            (definitions of stages should by found in <config>/recipe.cfg""")
    a.add_argument('-play', dest='play', action="store_true", required=False, default=False, \
                    help=" play audio after synthesis")
    a.add_argument('-lab', dest='make_label', action="store_true", default=False, \
                    help= "make label file as well as wave in output location")
    a.add_argument('config', help="""configuration to use: naive, semi-naive, gold, 
                                    as defined in <ROOT>/recipes/<config> -directory""")
    a.add_argument('files', nargs='*', help="text files to speak, reading from stdin by default")
    opts = a.parse_args()

    
    
    voice_location = os.path.join(dirs['VOICES'], opts.lang, opts.speaker, opts.config)
    train_location = os.path.join(dirs['TRAIN'], opts.lang, "speakers", opts.speaker, opts.config)
    config_path = os.path.join(dirs['CONFIG'], opts.config)
    voice_config = os.path.join(config_path, fname.RECIPE)


    stage = 'runtime'
    if opts.input_wav:
        stage = 'runtime_natural_duration'


    ## Make Voice object to contain voice elements trained on this corpus:
    voice = Voice(opts.speaker, opts.lang, opts.config, stage, dirs)


    if not opts.output:
        output_dir = os.path.join(voice_location, 'output', 'wav')
    else:
        output_dir = opts.output

    if not os.path.isdir(opts.output_utt):
        os.makedirs(opts.output_utt)

    for filename in opts.files:
       base=get_basename(filename)
       input_wavefile = None
       if opts.input_wav:
           input_wavefile = os.path.join(opts.input_wav, base + '.wav')
       output_uttfile = os.path.join(opts.output_utt, base + '.utt')
       text = ' '.join(readlist(filename))
       print text
       print base
       voice.synth_utterance(text, input_wavefile=input_wavefile, output_uttfile=output_uttfile)

        
def get_lang(elem) :
    """ Returns the language for a given element.
    If the element doesn't define a language, the language of the parent is used. """
    cur = elem
    while cur and not cur.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") :
        cur = cur.getparent()
        
    if cur is None:
        return None
    else:
        return cur.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")

        
def get_interpret_as(self, elem) :
    """ Returns a name of a rule based on the interpret_as element if such is valid
    for this element. Otherwise returns None. """
    cur = elem
    while (cur is not None and cur.tag != "say_as") :
        cur = cur.getparent()
    
    if cur is None: return None

    return cur.attrib.get("interpret_as")

    
if __name__=="__main__":

    main_work()
