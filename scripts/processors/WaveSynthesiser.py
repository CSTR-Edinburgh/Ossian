#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

from UtteranceProcessor import *
from util.NodeProcessors import *

from distutils.spawn import find_executable

class WaveSynthesiser(UtteranceProcessor):

    '''
    As with AcousticModel, this class needs to be generalised to glottHMM etc.
    '''

    def load(self): 
        pass
#         ## Check necessary binaries are on system path:       
#         for tool in ["synthesis_fft", "x2x", "mgc2sp"]:  
#             if not find_executable(tool):
#                 sys.exit("Binary %s must be on system path"%(tool))

    def process_utterance(self, utt):

        if utt.has_attribute("waveform"):    
            print "Utt has a natural waveform -- don't synthesise"
            return
            
        ## Check we've got everything to synthesise with:
        for filetype in ["gen_f0", "gen_mcep", "gen_bndap"]:
            if not utt.has_external_data(filetype):
                print 'Utterance does not have filetype %s associated with it -- cannot synthesise a wave'%(filetype)
                return

        fzero = utt.get_filename("gen_f0")
        mcep  = utt.get_filename("gen_mcep")
        bndap = utt.get_filename("gen_bndap")
        
        ## TODO: !!! fix hardcoded values here !!!
        shift = 5
        rate = 48000
        alpha = "0.77"  ## Assume 48kH and Bark cepstrum (Julius)      <<-- this should be shared from vocoder config!!
        gamma = "0"  ## for mcep
        order = "59"
        fft_len = "2048"

        ## convert params:
        comm = "x2x +fd %s > %s.double"%( bndap, bndap)
        #print comm
        os.system(comm)
        comm = "x2x +fa %s > %s.txt"%(fzero, fzero)
        #print comm
        os.system(comm)
        comm = "mgc2sp -a %s -g %s -m %s -l %s -o 2 %s | x2x +fd > %s.spec.double"%(alpha, gamma, order, fft_len, mcep, mcep)

        #print comm
        os.system(comm)

        gen_wav = utt.get_filename("gen_wav")

        comm = "%s "%("synthesis_fft") # self.RESYNTH_BIN)
        comm += "  -f %s "%(rate)
        comm += "  -fftl %s "%(fft_len)
        comm += "  -spec "
        comm += "  -order %s "%(order)
        comm += "  -shift %s "%(shift)
        comm += "  -sigp %s "%(1.2)
        comm += "  -sd %s "%(0.5)
        comm += "  -cornf %s "%(4000)
        comm += "  -bw %s "%(70.0)
        comm += "  -delfrac %s "%(0.2)
        comm += "  -bap "
        comm += "  -apfile %s.double "%(bndap)
        comm += "  %s.txt "%(fzero)
        comm += "  %s.spec.double "%(mcep)
        comm += "  %s > %s"%(gen_wav, gen_wav.replace(".wav", ".log"))

        #print comm
        os.system(comm)

        assert os.path.isfile(gen_wav)



    ## def train -- not necessary for vocoder (yet).


