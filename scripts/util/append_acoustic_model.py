#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

import sys
#import re
import naive.naive_util

from main.Voice import *

from main.AcousticModel import *
from processors.WaveSynthesiser import *
from processors.WavePlayer import *

def main_work():

    #################################################

    # ======== Get stuff from command line ==========

    def usage():
        print "Usage: ......  "
        sys.exit(1)

    # e.g. 

    try:

        voice_config = sys.argv[1]
        voice_components = sys.argv[2]
        ENGINE_BIN = sys.argv[3]      
        RESYNTH_BIN = sys.argv[4]  
        trained_model_dir = sys.argv[5]  


    except:
        
        usage()



    #################################################
    sys.path.append("/afs/inf.ed.ac.uk/user/o/owatts/naive/script/")
    #################################################


    ## Lots of these paths should be interpolated from system-wide options (e.g. bin dir etc).
    ## Absolute paths for now.
    context_file_location = "/afs/inf.ed.ac.uk/user/o/owatts/naive/context_files/"
    ESTDIR = "/group/project/nlp-speech/bin/"
    HTSDIR = "/afs/inf.ed.ac.uk/user/o/owatts/repos/simple4all/CSTRVoiceClone/trunk/bin/"
    SCRIPT = "/afs/inf.ed.ac.uk/user/o/owatts/naive/script"
    GENSIM_LOCATION = "%s/gensim-0.5.0/src/"%(SCRIPT)
    #################################################

    sys.path.append( GENSIM_LOCATION ) ## add gensim to path
    from VSMTagger import VSMTagger



    print " -- Open the existing voice"

    voice = Voice(config_file=voice_config)


    print " -- Make an utterance processor from a (trained) acoustic model   "

    ### This will only perform work where an utt does not have a wavefile attached:
    parameter_generator = AcousticModel(config_file=voice_components + "/parameter_generator.cfg",
                                    processor_name = "parameter_generator",
                                    ENGINE_BIN=ENGINE_BIN,
                                    model_location = trained_model_dir,
                                    HTSDIR=HTSDIR )
    parameter_generator.save()



    ### WAVESYNTH
    waveform_synthesiser = WaveSynthesiser(config_file=voice_components + "/waveform_synthesiser.cfg",
                                    processor_name = "waveform_synthesiser",
                                    RESYNTH_BIN=RESYNTH_BIN,                                    
                                    HTSDIR=HTSDIR )
    waveform_synthesiser.save()


    ### WAVE PLAYER (call e.g. sox etc)
    wave_player = WavePlayer(config_file=voice_components + "/wave_player.cfg",
                                    processor_name = "wave_player"
                             )
    wave_player.save()

    voice.add_processor(voice_components + "/parameter_generator.cfg")
    voice.add_processor(voice_components + "/waveform_synthesiser.cfg")
    voice.add_processor(voice_components + "/wave_player.cfg")

    print " -- Save voice"
    voice.save()

    print " -- Synthesize a test utterance (from some Spanish text...)"
    ## Use the voice to synth a test utterance:
    voice.synth_utterance("Esto es: una prueba.")




if __name__=="__main__":

    main_work()
