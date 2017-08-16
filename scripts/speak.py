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

import timeit

def start_clock(comment):
    print '%s... '%(comment),
    return (timeit.default_timer(), comment)

def stop_clock((start_time, comment), width=40):
    padding = (width - len(comment)) * ' '
    print '%s--> took %.2f seconds' % (padding, (timeit.default_timer() - start_time))  ##  / 60.)  ## min


def main_work():

    #################################################

    # root is one level below this file in directory structure, ie. below the 'scripts' folder
    ROOT = os.path.split(os.path.realpath(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))))[0]+'/'
    
    dirs = {
        'ROOT': ROOT,
        'CONFIG': ROOT + "configs/",
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
    a.add_argument('-t', dest='stage', required=False, default="runtime", \
                    help=""" defines the current usage stage 
                            (definitions of stages should by found in <config>/recipe.cfg""")
    a.add_argument('-play', dest='play', action="store_true", required=False, default=False, \
                    help=" play audio after synthesis")
    a.add_argument('-lab', dest='make_label', action="store_true", default=False, \
                    help= "make label file as well as wave in output location")
    a.add_argument('config', help="""configuration to use: naive, semi-naive, gold, 
                                    as defined in <ROOT>/recipes/<config> -directory""")
    a.add_argument('-bin', dest='custom_bindir')                                     
    a.add_argument('files', nargs='*', help="text files to speak, reading from stdin by default")
    opts = a.parse_args()

    
    if opts.custom_bindir != None:
        dirs['BIN'] = opts.custom_bindir 
        
            
    voice_location = os.path.join(dirs['VOICES'], opts.lang, opts.speaker, opts.config)
    train_location = os.path.join(dirs['TRAIN'], opts.lang, "speakers", opts.speaker, opts.config)
    config_path = os.path.join(dirs['CONFIG'], opts.config)
    voice_config = os.path.join(config_path, fname.RECIPE)


    ## Make Voice object to contain voice elements trained on this corpus:
    voice = Voice(opts.speaker, opts.lang, opts.config, opts.stage, dirs)



    if not opts.output:
        output_wavefile = os.path.join(voice_location, 'output', 'wav', 'temp.wav')
    else:
        output_wavefile = opts.output

    if not opts.output:
        output_labfile = None
    else:
        output_labfile = output_wavefile.replace('.wav', '.lab')

    prevspace = False
    para = []
    # Go through the files a paragraph at a time, unless it's SSML in which case we parse it
    # An empty line marks the change of paragraphs in plain text files
    for line in fileinput.input(opts.files):
       line = line.decode('utf-8').rstrip()
       t = start_clock('Synthesise sentence')
       print line
       if fileinput.isfirstline():
           if para != []:
               voice.synth_utterance(''.join(para), output_wavefile=output_wavefile, \
                            output_labfile=output_labfile)
               if opts.play:
                   os.system('play ' + output_wavefile)
               para = []
           line = line.lstrip()
           if line.startswith('<speak') or line.startswith('<xml'):
               tree = etree.parse(fileinput.filename())
               parseSSML(tree, voice)
               fileinput.nextfile()
           else: para.append(line)
       elif line.isspace(): prevspace = True
       elif prevspace and para != []:
           voice.synth_utterance(''.join(para), output_wavefile=output_wavefile, \
                            output_labfile=output_labfile)
           prevspace = False
           para = [line]
       else:
           para.append(line)

    if para != []:
       voice.synth_utterance(''.join(para), output_wavefile=output_wavefile, \
                            output_labfile=output_labfile)
       if opts.play:
           os.system('play ' + output_wavefile)
    stop_clock(t)

def parseSSML(tree, voice):
    """ Parses an SSML file and normalizes the text there. """
    prev_lang = None

    for elem in tree.getiterator() :
        lang = get_lang(elem)
        #TODO: react on the element type
        
        if lang is not None:
            voice.config['language'] = lang
        intr = get_interpret_as(elem)
        if intr is not None or voice.res.has_key('interpret_as'):
            voice.res.add_resource('interpret_as', intr)
            
        instr = elem.text
        voice.synth_utterance(instr)

        
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
