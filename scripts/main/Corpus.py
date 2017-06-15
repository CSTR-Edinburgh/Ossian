#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

import os
import sys
import re
from naive.naive_util import *
from Utterance import *

class Corpus():
    def __init__(self, filelist):
        """
        All files in filelist must exist and end in .txt or .wav. No specific order
        is required in the list -- .txt and .wav files are paired based on their
        names (i.e. /some-path/utt1.txt is paired with /some-other-path/utt1.wav).
        Unpaired txt files are used as unannotated text data.
        """
        self.utterances = {}

        ## remove 'files' beginning with "." from the list -- this is to avoid 
        ## trying to treat .svn directories as data in the toy example datasets:
        filelist = [fname for fname in filelist if not os.path.split(fname)[-1].startswith(".")]

        for fname in filelist:

            assert os.path.isfile(fname),"File %s does not exist"%(fname)
            assert fname.endswith(".txt") or fname.endswith(".wav"),"File %s does not end with .txt or .wav"%(fname)
            utt_name = get_basename(fname)
            if utt_name not in self.utterances:
                self.utterances[utt_name] = {}
            abs_fname = os.path.abspath(fname)
            if fname.endswith(".txt"):
                assert "text" not in self.utterances[utt_name],"More than 1 text file specified for utterance %s"%(utt_name)
                self.utterances[utt_name]["text"] = abs_fname
            elif fname.endswith(".wav"):
                assert "speech" not in self.utterances[utt_name],"More than 1 wave file specified for utterance %s"%(utt_name)
                self.utterances[utt_name]["speech"] = abs_fname

    def has_text(self, utt):        
        '''
        xxx
        '''
        assert utt in self.utterances,"Utterance %s not in collecvtion"%(utt)
        if "text" in self.utterances[utt]:
            return True
        else:
            return False

    def has_speech(self, utt):        
        assert utt in self.utterances,"Utterance %s not in collection"%(utt)
        if "speech" in self.utterances[utt]:
            return True
        else:
            return False

    def has_text_and_speech(self, utt):        
        assert utt in self.utterances,"Utterance %s not in collection"%(utt)
        if "text" in self.utterances[utt] and "speech" in self.utterances[utt]:
            return True
        else:
            return False

    def get_aligned(self):
        """Get subset of utterances that have text and speech"""
        return [utt for utt in self.utterances.keys() if self.has_text_and_speech(utt)]

    def get_text_only(self):
        """Get subset of utterances that have text but no speech"""
        return [utt for utt in self.utterances.keys() if self.has_text(utt) \
                                                        and not self.has_speech(utt) ]
        
    def all_text_files(self):
        utts_with_text = [utt for utt in self.utterances.keys() if self.has_text(utt)]
        return [self.utterances[utt]["text"] for utt in utts_with_text]

    def all_speech_files(self):
        utts_with_speech = [utt for utt in self.utterances.keys() if self.has_speech(utt)]
        return [self.utterances[utt]["speech"] for utt in utts_with_speech]    

   


#     def make_utterances(self, outdir, clear_old_data=False):
#         """
#         Initialise utt structures for utterances with both text and speech.
#         Save to directory, return list of (absolute) utterance filenames.
#         """
#         filelist = []
#         utt_list = self.get_aligned()
#         utts = [Utterance(self.utterances[utt]["text"], \
#             speech_file=self.utterances[utt]["speech"], utterance_location=outdir) for utt in utt_list]
# 
#         for (name, utt_struct) in sorted(zip(utt_list, utts)):
#             fname = os.path.join(outdir, name + ".utt")
#             filelist.append(fname)
#             if clear_old_data or not os.path.isfile(fname):
#                 utt_struct.save() 
#         return filelist
# 
#     ## try out processing text only with XML -- if OK, merge this and make_utterances
#     def make_text_only_utterances(self, outdir, clear_old_data=False):
#         """
#         Initialise utt structures for utterances with text only.
#         Save to directory, return list of (absolute) utterance filenames.
#         """
#         filelist = []
#         utt_list = self.get_text_only()
#         utts = [Utterance(self.utterances[utt]["text"], utterance_location=outdir, \
#                                          check_single_text_line=False) for utt in utt_list]
# 
#         for (name, utt_struct) in sorted(zip(utt_list, utts)):
#             fname = os.path.join(outdir, name + ".utt")
#             filelist.append(fname)
#             if clear_old_data or not os.path.isfile(fname):
#                 utt_struct.save() 
#         return filelist

    def make_utterances(self, outdir, clear_old_data=False):
        """
        Initialise utt structures for utterances with both text and speech.
        Save to directory, return list of (absolute) utterance filenames.
        """
        filelist = []
        
        utt_list_speech = self.get_aligned()

        utts_speech = [Utterance(self.utterances[utt]["text"], \
            speech_file=self.utterances[utt]["speech"], utterance_location=outdir) \
                                                                for utt in utt_list_speech]
                                                                
        utt_list = utt_list_speech 
        utts = utts_speech

        for (name, utt_struct) in sorted(zip(utt_list, utts)):
            fname = os.path.join(outdir, name + ".utt")
            filelist.append(fname)
            if clear_old_data or not os.path.isfile(fname):
                utt_struct.save() 
        return filelist
