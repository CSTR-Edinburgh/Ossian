#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi

import math 
import os
import glob
import numpy
import sys

from util.speech_manip import get_speech, put_speech
from naive.naive_util import readlist, writelist, add_htk_header
from UtteranceProcessor import SUtteranceProcessor
import default.const as c


## Check required executables are available:
from distutils.spawn import find_executable

required_executables = ['sox', 'perl']

for executable in required_executables:
    if not find_executable(executable):
        sys.exit('%s command line tool must be on system path '%(executable))
    
    

def get_world_fft_and_apdim(sample_rate):
    ## these are computed by World internally on the basis of sample rate
    ## and 2 constants set in src/world/constantnumbers.h 
    kFrequencyInterval = 3000.0
    kUpperLimit = 15000.0  
    apsize= int(min(kUpperLimit, (( sample_rate / 2.0) - kFrequencyInterval)) / kFrequencyInterval)
    
    ## replicate GetFFTSizeForCheapTrick in src/cheaptrick.cpp:
    kLog2 = 0.69314718055994529  # set in src/world/constantnumbers.h 
    f0_floor = 71.0  ## set in analysis.cpp
    fftl = math.pow(2.0, (1.0 + int(math.log(3.0 * sample_rate / f0_floor + 1) / kLog2)))

    return(fftl, apsize)

          
            
class WorldExtractor(SUtteranceProcessor):

    '''
    doesn't subclass FeatureExtractor because no config template used
    '''

    def __init__(self, processor_name='world_extractor', input_filetype='wav', output_filetype='cmp', \
                    coding_config={'order': 39, 'static_window': '1', 'delta_window': '-0.5 0.0 0.5', \
                    'delta_delta_window': '1.0 -2.0 1.0'}, sample_rate=16000, alpha=0.42, mcep_order=39,
                    frameshift_ms=5, resynthesise_training_data=False):  

        self.processor_name = processor_name
        self.input_filetype = input_filetype
        self.output_filetype = output_filetype
        self.coding_config = coding_config
        self.sample_rate = sample_rate
        self.rate = self.sample_rate
        self.alpha=alpha
        self.order=mcep_order
        self.frameshift_ms = frameshift_ms
        self.resynthesise_training_data = resynthesise_training_data
 

        super(WorldExtractor, self).__init__()


            
    def verify(self, voice_resources):
        self.voice_resources = voice_resources

        required_executables = ['analysis', 'synth', 'x2x', 'sopr', 'mcep']
        self.tool = self.voice_resources.get_path(c.BIN)
        for executable in required_executables:
            full_path = os.path.join(self.tool, executable)
            if not os.access(full_path, os.X_OK):
                sys.exit('%s must exist and be executable to use WorldExtractor'%(full_path))
            


    def do_training(self, speech_corpus, text_corpus):

        ## "training" an extractor involves writing a config, and establishing the location of resources etc.

        ## Write also desciption of .cmp files in terms of streams, stream widths to be used by alignment and acoustic model
        self.acoustic_feats = self.get_location()+"/acoustic_feats.cfg"
        self.tool = self.voice_resources.get_path(c.BIN)

        for toolname in ['analysis', 'synth']:
            path = os.path.join(self.tool, toolname)
            assert os.path.isfile(path), '%s does not exist'%(path)
            assert os.access(path, os.X_OK), '%s is not executable'%(path)

           
        self.fftl, self.apsize = get_world_fft_and_apdim(self.sample_rate)

        # make acoustic modelling config
        self.feats = ['mgc','lf0','bap']
        
        self.stream_sizes = [str(self.order+1),'1',str(self.apsize)]
        weights = ['1','0','0']
        msd = ['0','1','0']
        floor_scale = ["0.01" for x in range (len(self.feats))]

        streams = []

        # modifications for MSD streams
        cur_stream_index = 1
        for i in range(len(self.feats)):
            if msd[i] == "1":
                self.stream_sizes[i] +=" 1 1" 
                weights[i] += " "+weights[i]+ " "+weights[i]
                floor_scale[i] +=" "+floor_scale[i]+" "+floor_scale[i]
                msd[i] = "1 1 1"
                streams.append(str(cur_stream_index)+"-"+str(cur_stream_index+2))
                cur_stream_index+=3
            else:
                streams.append(str(cur_stream_index))
                cur_stream_index+=1

        # save these for acoustic model training with cmps
        htk_feats = open(self.acoustic_feats, "w")
        htk_feats.write("STREAMS=\"%s\"\n" % " ".join(streams))
        htk_feats.write("STREAM_NAMES=\"%s\"\n" % " ".join(self.feats))
        htk_feats.write("SHORT_STREAM_NAMES=\"1 2 5\"\n") #  % " ".join([str(i+1) for i in range(len(self.feats))]))     #      
        htk_feats.write("STATIC_STREAM_SIZES=\"%s\"\n" % " ".join(self.stream_sizes))
        htk_feats.write("MSD_STREAM_INFO=\"%s\"\n" % " ".join(msd))
        htk_feats.write("STREAM_WEIGHTS=\"%s\"\n" % " ".join(weights))
        htk_feats.write("VFLOORSCALESTR=\"Vector %d %s\"\n" % (len(" ".join(self.stream_sizes).split())," ".join(floor_scale)))
        htk_feats.close()

        ## Make delta window coefficients in config file into separate files:
        training_dir = self.get_training_dir()
        self.winfiles = []
        for window in ['static_window', 'delta_window', 'delta_delta_window']:
            fname = os.path.join(training_dir, window + '.win')
            data = self.coding_config[window]
            length = len(data.strip().split())
            data = '%s %s'%(length, data)
            writelist([data], fname)
            self.winfiles.append(fname)
        

    def process_utterance(self, utt):
        
        ## If there is no waveform attached to the utt, don't do anything:        
        if not utt.has_attribute("waveform"):
            return 



        ## Add some data to the utt structure recording the structure of the 
        ## associated acoustic features we've produced. Do this first, in case
        ## we use existing features.
        self.stream_sizes[1] = '1'  ## otherwise '1 1 1' for F0    TODO: fix this nicely!
        utt.add_acoustic_stream_info(self.feats, self.stream_sizes)

        ## If a feature file already exists, skip:
        if utt.has_external_data(self.output_filetype):
            ##  TODO: check description against existing feats?
            return
            
        ## else extract features
        infile = utt.get("waveform")
        outfile = utt.get_filename(self.output_filetype)

        ## strip suffix .cmp:-
        assert outfile.endswith('.' + self.output_filetype)
        chars_to_strip = len(self.output_filetype)+1
        outstem = outfile[:-chars_to_strip]


        rate = self.rate
        sample_rate=self.rate
        alpha=self.alpha
        order=self.order
        fftl=self.fftl
        apsize=self.apsize    
        frameshift_ms=self.frameshift_ms 

        script_dir = self.voice_resources.path[c.SCRIPT]  
        
        ## 1) remove wave header, downsample etc. with sox:
        comm = "sox -t wav " + infile
        comm += " -c 1 -e signed-integer "
        comm += " -r %s"%(rate)
        comm += " -b 16 "  
        comm += " " + outstem + ".wav"
        comm += " dither"   ## added for hi and rj data blizz 2014
        success = os.system(comm)
        if success != 0:
            print 'sox failed on utterance ' + utt.get("utterance_name")
            return
       
        comm = "%s/analysis %s.wav %s.f0.double %s.sp.double %s.bap.double > %s.log"%(self.tool, outstem, outstem, outstem, outstem, outstem)
        success = os.system(comm)
        #print comm
        if success != 0:
            print 'world analysis failed on utterance ' + utt.get("utterance_name")
            return
       
        if self.resynthesise_training_data:
            ## resynthesis to test
            comm = "%s/synth %s %s %s.f0.double %s.sp.double %s.bap.double %s.resyn.wav > %s.log"%(self.tool, fftl, rate, outstem, outstem, outstem, outstem, outstem)
            success = os.system(comm)
            if success != 0:
                print 'world synthesis failed on utterance ' + utt.get("utterance_name")
                return       
       
        comm = "%s/x2x +df %s.sp.double | %s/sopr -R -m 32768.0 | %s/mcep -a %s -m %s -l %s -j 0 -f 0.0 -q 3 > %s.mgc"%(self.tool, outstem, self.tool, self.tool, alpha, order, fftl, outstem)
        ## -e 1.0E-8
        success = os.system(comm)
        if success != 0:
            print 'conversion of world spectrum to mel cepstra failed on utterance ' + utt.get("utterance_name")
            return    
        
        for stream in ['bap']:
            comm = "%s/x2x +df %s.%s.double > %s.%s"%(self.tool, outstem, stream, outstem, stream)
            success = os.system(comm)
            if success != 0:
                print 'double -> float conversion (stream: '+stream+') failed on utterance ' + utt.get("utterance_name")
                return    

        for stream in ['f0']:
            comm = "%s/x2x +da %s.%s.double > %s.%s.txt"%(self.tool, outstem, stream, outstem, stream)
            success = os.system(comm)
            if success != 0:
                print 'double -> ascii conversion (stream: '+stream+') failed on utterance ' + utt.get("utterance_name")
                return                        
                    
        ## 5) F0 conversion:
        f0 = [float(val) for val in readlist(outstem + '.f0.txt')]
        log_f0 = []
        for val in f0:
            if val == 0.0:
                log_f0.append('-1.0E10')
            else:
                log_f0.append(math.log(val))
        writelist(log_f0, outstem + '.f0.log')
        
        comm = "%s/x2x +af %s.f0.log > %s.lf0"%(self.tool, outstem, outstem)
        success = os.system(comm)
        if success != 0:
            print 'writing log f0 failed on utterance ' + utt.get("utterance_name")
            return
            
        ## add mcep/ap/f0 deltas:
        for (stream,dimen) in [('mgc', order+1), ('bap', apsize), ('lf0', 1)]:
            comm = "perl %s/window.pl %s "%(script_dir, dimen)
            comm += "%s.%s %s > %s.%s.delta"%(outstem, stream, ' '.join(self.winfiles), outstem, stream)
            success = os.system(comm)
            if success != 0:
                print 'delta ('+stream+') extraction failed on utterance ' + utt.get("utterance_name")
                return
  
        ### combined streams:--        
        ap = get_speech(outstem + '.bap.delta', apsize*len(self.winfiles))  
        mgc = get_speech(outstem + '.mgc.delta', (order+1)*len(self.winfiles))     
        lf0 = get_speech(outstem + '.lf0.delta', 1*len(self.winfiles))  
        cmp = numpy.hstack([mgc, lf0, ap])
        put_speech(cmp, outfile)

        ## 7) add header
        floats_per_frame = (order+2 + apsize) * len(self.winfiles)    ## +2 for energy and F0
        add_htk_header(outfile, floats_per_frame, frameshift_ms)
        
        ## 8) tidy:
        self.extensions_to_keep = ['.'+self.output_filetype, '.f0.txt']   ## TODO: make configuable?
        self.extensions_to_keep.append('.resyn.wav')
        self.extensions_to_keep.extend(['.mgc','.bap','.lf0'])
        
        keepfiles = [outstem + ending for ending in self.extensions_to_keep]
        
        for junk in glob.glob(outstem + '.*'):
            if not junk in keepfiles:
                os.remove(junk)



####### TODO: revise other feature extractors ##########
"""



## General class for extracting features using arbitrary tools
class FeatureExtractor(UtteranceProcessor):
    '''
    General class for calling tools to extract acoustic features. Unusually, we will 
    record default settings of config variables in an external config file rather than in
    the code. This exception is because many feature extraction tools have *lots* of config
    variables, and perhaps putting all the defaults in the code is messy? TODO: consider this...
    '''
    def load(self):

        self.input_filetype = self.config.get('input_filetype', 'wav')
        self.output_filetype = self.config.get('output_filetype', 'acoustic_features')
        
        ## Find location of config_template relative to this file:
        self.template_location = os.path.abspath(os.path.dirname(__file__)+"/../../config_templates/")
        instances_classname = self.__class__.__name__
        self.template_file = os.path.join(self.template_location, instances_classname + ".cfg")       
        if not os.path.isfile(self.template_file):
            sys.exit("%s doesn't exist -- can't find template config for object of class %s"%(self.template_file, instances_classname))
        
        ## Load default values:
        self.coding_config = ConfigObj(self.template_file, encoding='UTF8', interpolation="Template")

        ## Overwrite with user-specified values from voice config:
        if 'coding_config' in self.config:
            for (key,value) in self.config['coding_config'].items():
                if key in self.coding_config:
                    self.coding_config[key] = value
                else:
                    sys.exit('Key in FeatureExtractor\'s coding_config not in template: %s'%(key))

        ## Write the config file which can actually be used for extraction by e.g. 
        ## STRAIGHT, GlottHMM, or HCopy
        training_dir = self.get_training_dir()
        self.config_for_coding = os.path.join(training_dir, 'config_for_coding.cfg')
        self.coding_config.filename = self.config_for_coding
        self.coding_config.write()

        ## Write also desciption of .cmp files in terms of streams, stream widths to be used by alignment and acoustic model
  
        self.acoustic_feats = self.get_location()+"/acoustic_feats.cfg"
        
        self.acoustic_config = ConfigObj(self.acoustic_feats, interpolation="Template") #,encoding='ASCII') #, encoding='UTF8')

class MFCCExtractor(FeatureExtractor):

    def load(self):  
    
        FeatureExtractor.load(self)
        self.config["ESTDIR"] = self.voice_resources.get_path(c.EST)  ## TODO
        self.config["HTSDIR"] = self.voice_resources.get_path(c.HTS)  # TODO


    def process_utterance(self, utt):

        ## TODO: change to use self.input_filetype, for now hardcoded. Change get_filename
        ## also to look in corpus if nothing in train?
        
        #             print utt.xpath('@waveform')
        #             print utt.get_filename('wav')
        #             print utt.get_filename('align_lab')
        #             sys.exit('test 56565')
        
        ## If there is no waveform attached to the utt, don't do anything:        
        if not utt.has_attribute("waveform"):
            return 

        ## If an mfcc file already exists, kip:
        if utt.has_external_data(self.output_filetype):
            return
            
        wavefile = utt.get("waveform")

        mfccfile = utt.get_filename(self.output_filetype)


        ### This sequence of conversions is very ugly! :--

        ## First fix bit depth with sox -- 24 bit makes ch_wave unhappy, and switch to mono: 
        command = "sox %s -c 1 -b 16 %s "%(wavefile, mfccfile+".16bit.wav")  ## ,  mfccfile + ".log")
        os.system(command)

        ## Convert to NIST and resample to 16000Hz if necessary
        command = "%s/ch_wave -otype nist -F 16000 -o %s %s > %s"%(self.config["ESTDIR"], mfccfile + ".wav", mfccfile+".16bit.wav",  mfccfile + ".log")
        os.system(command)
        
        ## Add a little random noise -- too many 0s in a row leads to:
        ## WARNING [-7324]  StepBack: Bad data or over pruning
        ## TODO: check sox on system path / use specific copy
        command = "sox %s %s dither "%(mfccfile + ".wav", mfccfile + "_dithered.nist")  ## ,  mfccfile + ".log")
        os.system(command)

        ## Make MFCCs
        command = "%s/HCopy -T 1 -C %s %s %s >> %s" % (self.config["HTSDIR"], self.config_for_coding,
                                                        mfccfile + "_dithered.nist", mfccfile, mfccfile + ".log")                                      
        os.system(command)
#        for ext in ["conf", "log", "wav"]:
#            os.system("rm -f %s.%s" % (mfccfile, ext))
#        os.system("rm " + mfccfile + "_dithered.nist")
#        os.system("rm " + mfccfile + ".16bit.wav")



class GlottExtractor(FeatureExtractor):
    '''
    Extracts glottHMM features
    '''
    
    def load(self):

        FeatureExtractor.load(self)
        assert len(self.config["weights"]) == len(self.config["feats"])==len(self.config["coeffs"])==len(self.config["msd"])
        
        self.feats = self.config["feats"]
        self.coeffs = self.config["coeffs"]
        feat_dict = {}
        for i in range(len(self.feats)):
            feat_dict[self.feats[i]] = self.coeffs[i]


        # Where to put pulse, hpfilter and pulselib files 
        # and where to set paths?
        
        glott_dir = self.voice_resources.get_path('GLOTT')
        print glott_dir
        self.coding_config["HPFILTER_FILENAME"] = glott_dir+"/"+self.coding_config["HPFILTER_FILENAME"]
        self.coding_config["GLOTTAL_PULSE_NAME"] = glott_dir+"/"+self.coding_config["GLOTTAL_PULSE_NAME"]
       
        assert os.path.isfile(self.coding_config["HPFILTER_FILENAME"]), "file %s not found" %(self.coding_config["HPFILTER_FILENAME"])
        assert os.path.isfile(self.coding_config["GLOTTAL_PULSE_NAME"]), "file %s not found" %(self.coding_config["GLOTTAL_PULSE_NAME"])
          
        
        # copy the main configuration
        #
        main_config_template = self.template_location+"/"+self.config["main_config"]
        assert os.path.isfile(main_config_template)

        self.main_config = self.get_location()+"/main_config.cfg"
        os.system("cp "+main_config_template+" "+self.main_config)
        
        
        # save user configs in libconfig style for GlottHMM
        #
        self.user_config = self.get_location()+"/user_config.cfg"
        conf_f = open(self.user_config,"w")
        glott_feat_names = {"LPC_ORDER":"LSF", "LPC_ORDER_SOURCE":"LSFSource", "HNR_CHANNELS": "HNR"}

        for (key,value) in self.coding_config.items():
            # training coeffs override analysis coeffs if specified in both
            if key in glott_feat_names and glott_feat_names[key] in feat_dict:
                value =feat_dict[glott_feat_names[key]]
            try:
                float(value)
                conf_f.write("%s = %s;\n" % (key, value))
                print "%s = %s;" % (key, value)
            except:
                conf_f.write("%s = \"%s\";\n" % (key, value))
                             
                
     
        # make acoustic modelling config
        stream_sizes = list(self.config["coeffs"])
        weights = self.config["weights"]
        msd = self.config["msd"]
        floor_scale = ["0.01" for x in range (len(self.feats))]

        streams = []

        # modifications for MSD streams
        cur_stream_index = 1
        for i in range(len(self.feats)):
            if msd[i] == "1":
                stream_sizes[i] +=" 1 1" 
                weights[i] += " "+weights[i]+ " "+weights[i]
                floor_scale[i] +=" "+floor_scale[i]+" "+floor_scale[i]
                msd[i] = "1 1 1"
                streams.append(str(cur_stream_index)+"-"+str(cur_stream_index+2))
                cur_stream_index+=3
            else:
                streams.append(str(cur_stream_index))
                cur_stream_index+=1

        # save these for acoustic model training with cmps
        htk_feats = open(self.acoustic_feats, "w")
        htk_feats.write("STREAMS=\"%s\"\n" % " ".join(streams))
        htk_feats.write("STREAM_NAMES=\"%s\"\n" % " ".join(self.feats))
        htk_feats.write("SHORT_STREAM_NAMES=\"%s\"\n" % " ".join([str(i+1) for i in range(len(self.feats))]))
        htk_feats.write("STATIC_STREAM_SIZES=\"%s\"\n" % " ".join(stream_sizes))
        htk_feats.write("MSD_STREAM_INFO=\"%s\"\n" % " ".join(msd))
        htk_feats.write("STREAM_WEIGHTS=\"%s\"\n" % " ".join(weights))
        htk_feats.write("VFLOORSCALESTR=\"Vector %d %s\"\n" % (len(" ".join(stream_sizes).split())," ".join(floor_scale)))

        
        # save also for synthesis
        #...
             
        # set windows, (same as SPTK, but windows not part of coding config..)
        self.winfiles = []
        for window in ['static_window', 'delta_window', 'delta_delta_window']:
            fname = os.path.join(self.get_training_dir(), window + '.win')
            data = self.config[window]
            length = len(data.strip().split())
            data = '%s %s'%(length, data)
            writelist([data], fname)
            self.winfiles.append(fname)

    def process_utterance(self, utt):
        if not utt.has_attribute("waveform"):
            return
        
        if utt.has_external_data(self.output_filetype):
            return

        script_dir = self.voice_resources.get_path(c.SCRIPT)
        bin_dir = self.voice_resources.get_path(c.BIN)
        glott_dir = self.voice_resources.get_path('GLOTT')
        infile = utt.get_filename(self.input_filetype)
        outfile = utt.get_filename(self.output_filetype)
        root = infile[:-len(self.input_filetype)-1]
                      
        
        ## First fix bit depth and s. rate with sox and switch to mono; add some dither: 
        ds_wav = utt.get_filename('wav')
      
        command = "sox %s -c 1 -b 16 -r 16000 %s dither"%(utt.get("waveform"), ds_wav)
        os.system(command)

        # perform GlottHMM analysis, resulting in LSF, SourceLSF, HNR, Gain and F0

        ### Check for everything at top of script:--
        analysis = glott_dir+"/Analysis"
        assert os.path.isfile(analysis), "%s+/Analysis not found, GlottHMM not installed?" % glott_dir
        command =  analysis+" "+ds_wav+" "+self.main_config+" "+self.user_config +">/dev/null"
        #if not (os.path.isfile(ds_wav+"/"+utt.get("utterance_name")+".LSF")):
        os.system(command)

      
        # convert to binary
        for type in self.feats:
            if type=="mcep":
                continue
            asc_f = root+"."+type
            bin_f = asc_f+".bin"
            success = os.system(bin_dir+"/x2x +af "+asc_f+" >"+bin_f)
            if success!=0:
                print "ascii to binary conversion on "+asc_f+" failed"
                sys.exit(-1)


        #for feat in ("LSF", "SourceLSF", "HNR", "Gain", "F0"):
        #    assert(os.path.isfile(ds_wav+"/"+utt.get("utterance_name")+"."+feat))

        
        #Convert LSF to mcep if specified
        if "mcep" in self.feats:
            os.system(bin_dir+"/x2x +af "+root+".lsf > "+root+".lsf.bin")
            
            n_lsf = self.coding_config["LPC_ORDER"]

            # warping 0.35
            ncoeff_mcep = str(int(self.config["mcep_order"])-1)
            ncoeff2 =(int(ncoeff_mcep)+1)
            # go back to lpc from lsf
            os.system(bin_dir+"/lsp2lpc -k -s 16 -i 0  -m "+n_lsf+" "+root+".lsf.bin > "+root+".lpc.bin")

            # add gain
            #os.system(bin_dir+"/merge +f -s 0 -l "+self.feats["LSF"]+" -L 1 "+root+".gain.bin < "+root+".lpc.bin >"+root+".lpc_g.bin")

            # convert lpc spectrum to warped cepstrum, use extra coefficients for warping (120)
            os.system(bin_dir+"/lpc2c -m "+n_lsf+" -M 120 "+root+".lpc.bin | "+bin_dir+"/freqt -a 0 -A 0.35 -m 120 -M "+ncoeff_mcep+" > "+root+".mcep.bin")
     
            # plot Tokuda-style to verify
            #os.system(bin_dir+"/bcut +f -n "+ncoeff_mcep+" -s 0 -e 500 "+root+".mcep.bin | "+bin_dir+"/mgc2sp -m "+ncoeff_mcep+" -a 0.35   -l 512 | "+ \
            #bin_dir+"/grlogsp -l 512 -x 8 | "+bin_dir+"/psgr -l > "+root+".mcep.ps")
            ## reconstuct lsf
            #freqt -> c2acr -> levdur
            
            
        
        
        # make htk cmp

        from numpy import loadtxt,savetxt,log

        # convert to binary and handle f0
        
        asc_f =root+".F0"

        # msd and log
        f0 = loadtxt(asc_f)
        f0[f0>0] =log(f0[f0>0])
        f0[f0==0.0] = -1.0E10
        savetxt(asc_f+".log", f0.astype('float'), fmt = '%.8f')
        success = os.system(bin_dir+"/x2x +af "+asc_f+".log "+ " >"+asc_f+".bin")
        if success != 0:
            print 'writing log f0 failed on utterance ' + utt.get("utterance_name")
            return
           
        # add windows
        
        for i in range(len(self.feats)):
            type = self.feats[i]
            asc_f = root+"."+type
            bin_f = asc_f+".bin"

            # add deltas
            delta_f = asc_f+".d"
            success = os.system("perl "+script_dir+"/window.pl "+self.coeffs[i]+ " "+bin_f+" "+(' '.join(self.winfiles))+" > "+delta_f)
            if success!=0:
                print "adding dynamic features to "+asc_f+" failed"

        # make cmp

        nwin = 3
        cmp_f = root+"."+self.feats[0]+".d"    
        sum_len = int(self.coeffs[0])*nwin

        for i in range(1, len(self.feats)):
            #cur_len = int(self.feats[self.feats[i]])*nwin

            cur_len = int(self.coeffs[i])*nwin

            in_f =  root+"."+self.feats[i]+".d"
            out_f = root+".cmp."+str(i)
            success = os.system(bin_dir+"/merge +f -s 0 -l "+str(cur_len)+" -L "+str(sum_len)+" "+cmp_f+" < "+in_f+" > "+out_f)
            sum_len +=cur_len
            cmp_f = out_f
        
           


        outfile = utt.get_filename(self.output_filetype)
        os.system("cp "+cmp_f+" "+outfile)
        # frameshift hardcoded 5ms
      
        add_htk_header(outfile, sum_len, 5)
       

        ## 8) tidy but save original analysis features for prosody annotation


        for junk in glob.glob(root + '.cmp.*'):
            os.remove(junk)
        for junk in glob.glob(root + '.*.bin'):
            os.remove(junk)
        for junk in glob.glob(root + '.*.d'):
            os.remove(junk)

class GlottGVCollector(FeatureExtractor):

    def load(self):
        self.param_dir = self.voice_resources.get_path(c.TRAIN, self.config["param_dir"])

    def train(self, speech_corpus):
        hts_dir = self.voice_resources.path[c.HTS] ## for SPTK!
        ordr = {'LSF': 31, 'LSFsource': 15, 'HNR': 5, 'F0': 1}
        gvdir = os.path.join(self.param_dir, 'gv')
        for typ in ['LSF', 'LSFsource', 'HNR', 'F0']:   
            os.system("%s/vstat -n %s -o 0 -d %s/gvdata.%s >%s/gv-%s.pdf"%(hts_dir, ordr[typ]-1, gvdir, typ, gvdir, typ))     
          
          
            
class SPTKExtractor(FeatureExtractor):

    def load(self):  
    
        FeatureExtractor.load(self)

        self.config["HTSDIR"] = self.voice_resources.get_path(c.BIN)  
        self.sptk = self.voice_resources.get_path(c.BIN)

        ## Make delta window coefficients in config file into separate files:
        training_dir = self.get_training_dir()
        self.winfiles = []
        for window in ['static_window', 'delta_window', 'delta_delta_window']:
            fname = os.path.join(training_dir, window + '.win')
            data = self.coding_config[window]
            length = len(data.strip().split())
            data = '%s %s'%(length, data)
            writelist([data], fname)
            self.winfiles.append(fname)
        
        


    def process_utterance(self, utt):
        
        ## If there is no waveform attached to the utt, don't do anything:        
        if not utt.has_attribute("waveform"):
            return 

        ## If a feature file already exists, skip:
        if utt.has_external_data(self.output_filetype):
            return
            
        ## else extract features
        
        infile = utt.get("waveform")
        outfile = utt.get_filename(self.output_filetype)
        
        
        cc = self.coding_config

        order = int(cc['order'])
        rate = int(cc['target_sample_rate'])
        sptk = self.sptk
        framelength = int(cc['framelength'])
        frameshift = int(cc['frameshift'])
        fft_length = int(cc['fft_length'])
        
        frameshift_ms = int(cc['frameshift_ms'])

        lo_f0 = int(cc['lo_f0'])
        hi_f0 = int(cc['hi_f0'])
        
        f0_method = cc['f0_method']
        if f0_method == 'swipe':
            f0_code = 1
        elif f0_method == 'rapt':
            f0_code = 0
        else:
            sys.exit('F0 method must be swipe or rapt: was %s'%(f0_method))
            
        script_dir = self.voice_resources.path[c.SCRIPT]  ## for window.pl


        ## 1) remove wave header, downsample etc. with sox:
        comm = "sox -t wav " + infile
        comm += " -c 1 -e signed-integer "
        comm += " -r %s"%(rate)
        comm += " -t raw " + outfile + ".raw"
        comm += " dither"   ## added for hi and rj data blizz 2014
        success = os.system(comm)
        if success != 0:
            print 'sox failed on utterance ' + utt.get("utterance_name")
            return
       

        ## 2) mel cepstral analysis with SPTK tools:
#        print '2'
        comm =  "%s/x2x +sf %s.raw | "%(sptk, outfile)  
        comm += "%s/frame -l %s -p %s | "%(sptk, framelength, frameshift)   
        comm += "%s/window -l %s -L %s -w 1 -n 1 | "%(sptk, framelength, fft_length)
        comm += "%s/mcep -a 0.42 -e 0.001 -m %s -l %s "%(sptk, order, fft_length)
        comm += " > %s.mcep"%(outfile)
        success = os.system(comm)
        if success != 0:
            print 'mcep extraction failed on utterance ' + utt.get("utterance_name")
            return
            
            
        ## 3) add mcep deltas:
#        print '3'
        comm = "perl %s/window.pl %s "%(script_dir, order+1)
        comm += "%s.mcep %s > %s.mcep.delta"%(outfile, ' '.join(self.winfiles), outfile)
        success = os.system(comm)
        if success != 0:
            print 'delta (mcep) extraction failed on utterance ' + utt.get("utterance_name")
            return

            
        ## 4) F0 extraction:
#        print '4'
        comm = "%s/x2x -o +sf %s.raw | "%(sptk, outfile)
        comm += "%s/pitch -a %s -s 16 -p %s "%(sptk, f0_code, frameshift)
        comm += "-L %s -H %s -o 1 | "%(lo_f0, hi_f0) 
        comm += "%s/x2x -o +fa  > %s.f0"%(sptk, outfile)
        success = os.system(comm)
        if success != 0:
            print 'f0 extraction failed on utterance ' + utt.get("utterance_name")
            return
            
            

        ## 5) F0 conversion & deltas:
#        print '5'
        f0 = [float(val) for val in readlist(outfile + '.f0')]
        log_f0 = []
        for val in f0:
            if val == 0.0:
                log_f0.append('-1.0E10')
            else:
                log_f0.append(math.log(val))
        writelist(log_f0, outfile + '.f0.log')
        
        comm = "%s/x2x +af %s.f0.log > %s.f0.log.bin"%(sptk, outfile, outfile)
        success = os.system(comm)
        if success != 0:
            print 'writing log f0 failed on utterance ' + utt.get("utterance_name")
            return
            
        comm = "perl %s/window.pl %s "%(script_dir, 1)
        comm += "%s.f0.log.bin %s > %s.f0.log.bin.delta"%(outfile, ' '.join(self.winfiles), outfile)
        success = os.system(comm)
        if success != 0:
            print 'delta (f0) extraction failed on utterance ' + utt.get("utterance_name")
            return



        ## 6) stack mcep and f0:
#        print '6'
        mcep_size = (order+1) * len(self.winfiles)
        nwin = len(self.winfiles)
        comm = "%s/merge +f -s 0 -l %s -L %s %s.mcep.delta"%(sptk, nwin, mcep_size, outfile)
        comm += " < %s.f0.log.bin.delta > %s"%(outfile, outfile)
        success = os.system(comm)
        '''
        ## This returns 1 even when running OK: 
          if success != 0:
              print 'stacking mcep and f0 failed on utterance ' + utt.get("utterance_name")
              return
        '''
     

        ## 7) add header
#        print '7'
        floats_per_frame = (order+2) * nwin    ## +2 for energy and F0
        add_htk_header(outfile, floats_per_frame, frameshift_ms)
        
    
        ## 8) tidy:
        for junk in glob.glob(outfile + '.*'):
            os.remove(junk)

"""
