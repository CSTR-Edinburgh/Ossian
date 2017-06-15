#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Antti Suni - Antti.Suni@helsinki.fi
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk

PI = 3


#directory constants
CONFIG = "config"
PROCESSOR = "processors"
MODEL = "models"
TRAIN = "train"
VOICE = "voice"
CORPUS = "corpus"
RULES = "rules"
CONTEXT_FEATS = "context_feats"
SCRIPT = "scripts"
SPEAKER ="speakers"
COMPONENT="components"
LANG = "lang"
BIN = "bin"
HTS = "htk"
EST = "speech_tools"
SPTK = "bin"

ACOUSTIC_MODELLING_SCRIPT = "acoustic_modelling_script"
ACOUSTIC_MODELLING_CONFIG = "acoustic_modelling_config"


#resource types
FILE = "file"
DIRECTORY = "dir"
STRING = "string"
FLAG = "flag"


# file manipulation

CREATE = "create"
REPLACE = "replace"
APPEND = "append"
DELETE = "delete"
BACKUP = "backup"

#possible units in utterance hierarchy from bottom

STATE = "state"
PHONE = "segment"
LETTER = "letter"
SYLLABLE = "syl"
MORPH = "morph"
SUBWORD = "subword"
WORD = "word"
TOKEN = "token"
XP = "xp"
PHRASE = "phrase"
UTTERANCE = "utt"
PARAGRAPH = "paragraph"
CHAPTER = "chapter"
TEXT = "text"

## osw: for utterance.py:
#UTTEND = "_UTTEND_"
TERMINAL = "_END_"
SKIP_MODEL_NAME = 'skip'  ## name of htk model with no emissions
PROB_PAUSE = '_PROB_PAUSE_'
POSS_PAUSE = '_POSS_PAUSE_'
