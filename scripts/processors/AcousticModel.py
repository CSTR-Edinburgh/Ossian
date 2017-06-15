#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Simple4All - January 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
## Contact: Antti Suni - Antti.Suni@helsinki.fi


from UtteranceProcessor import SUtteranceProcessor
from util.NodeProcessors import *
from FeatureExtractor import get_world_fft_and_apdim

from distutils.spawn import find_executable

from naive.naive_util import readlist
from util.speech_manip import get_speech,put_speech

import shutil
import numpy as np
import numpy 

import time

class AcousticModel(SUtteranceProcessor):
    '''
    Specific to STRAIGHT -- TODO: make a more general AcousticModel and subclass it for 
    STRAIGHT, glottHMM, etc.?
    Or can we code the stream names in config, and have this class agnostic about number
    and names of streams? Some special cases, like VUV?
    '''
    def __init__(self, processor_name='acoustic_model', input_label_filetype='lab', acoustic_feature_filetype='cmp', output_filetype='wav', \
            question_file_name='questions.hed', acoustic_subrecipe='standard_voicebuild', \
            training_settings={}, vuv=0.50, speech_coding_config={}, scale_var=1.2, postfilter_coeff=0.0, \
            speech_rate=1.0, sample_rate=16000, alpha=0.42, mcep_order=39): #, frameshift_ms=5): 

        self.processor_name = processor_name
        self.input_label_filetype = input_label_filetype
        self.acoustic_feature_filetype = acoustic_feature_filetype
        self.output_filetype = output_filetype
        self.question_file_name = question_file_name
        self.acoustic_subrecipe = acoustic_subrecipe
        self.training_settings = training_settings
        self.vuv = vuv ## high means more unvoiced
        self.speech_coding_config = speech_coding_config
        self.scale_var = scale_var
        self.postfilter_coeff = postfilter_coeff
        self.speech_rate = speech_rate

        self.sample_rate = sample_rate
        self.alpha = alpha
        self.mcep_order = mcep_order


        super(AcousticModel, self).__init__()


    def verify(self, resources):
        super(AcousticModel, self).verify(resources)

        ## Set path to HTS binaries from voice resources:
        self.hts_dir = self.voice_resources.path[c.BIN]

       ## Try loading model:
        self.trained = True
        self.model_dir = os.path.join(self.get_location()) 

        
        if not os.path.isdir(self.model_dir):
            self.trained = False
            
            
        ## verify all the parts needed are present: if the model files exists, count it as trained:
        complete = True
        
        #for component in ['tree-logF0.inf', 'tree-mcep.inf', \
        #                  'duration.pdf', 'logF0.pdf', 'mcep.pdf']:
        ## ANT: until stream generalization is done, just check duration
        for component in ['tree-duration.inf', 'duration.pdf']:
            if not os.path.isfile(os.path.join(self.model_dir, component)):
                complete = False
                self.trained = False
                #print 'component missing: %s'%(component)

        ### TODO: share in python config
        ## get training configuration defined in feature extractor, for glotthmm
        self.stream_definitions = ConfigObj(self.get_location()+"/../acoustic_feature_extractor/acoustic_feats.cfg")

        self.winfiles = []
        for (window, default_window) in [  ('static_window', '1.0'),  \
                                           ('delta_window', '-0.5 0.0 0.5'), \
                                           ('delta_delta_window', '1.0 -2.0 1.0')]:
            fname = os.path.join(self.get_location(), window + '.win')
            data = self.speech_coding_config.get(window, default_window)
            length = len(data.strip().split())
            data = '%s %s'%(length, data)
            writelist([data], fname)
            self.winfiles.append(fname)


    def process_utterance(self, utt):  ### sptk for engine 1.07:

        if utt.has_attribute("waveform"):    
            #print "Utt has a natural waveform -- don't synthesise"
            return
            
        if not self.trained:
            print 'WARNING: Cannot apply processor %s till model is trained'%(self.processor_name)
            return


        label = utt.get_filename(self.input_label_filetype) 
        owave = utt.get_filename(self.output_filetype)
        
        comm = self.hts_dir + '/hts_engine'
        
        comm += "  -td %s/tree-duration.inf "%(self.model_dir)
        comm += "  -md %s/duration.pdf "%(self.model_dir)
        
        comm += "  -tf %s/tree-logF0.inf "%(self.model_dir)
        comm += "  -mf %s/logF0.pdf "%(self.model_dir)
        
        comm += "  -tm %s/tree-mcep.inf "%(self.model_dir)
        comm += "  -mm %s/mcep.pdf "%(self.model_dir)
        
        ## windows:
        for stream in ['f', 'm']:
            for winfile in self.winfiles:
                comm += "  -d%s %s "%(stream, winfile)

        comm += " -b 1.5 " ## for postfiltering 
        comm += "  -u %s "%(self.vuv)
        comm += "  -ow %s "%(owave)
        comm += "    %s > %s.log"%(label, label)
        
        os.system(comm)

   
      
    def do_training(self, speech_corpus, text_corpus):
        """
        This is nearly identical to Aligner's method of the same name -- how to refactor?
        Differences -- question_file, messages (aligner -> AM)
        """

        self.verify(self.voice_resources) ## to get stream definitions in place

        ## Double check not trained:
        if self.trained:
            print "Acoustic model already trained!"
            return


        ## Else proceed to training:


        train_location = self.model_dir + "/training"        
        print "\n          Training acoustic model -- see %s/log.txt\n"%(train_location) 
        if os.path.isdir(train_location):
            shutil.rmtree(train_location)  ## delete any existing stuff for a clean start
        os.makedirs(train_location)
      
        feature_dir = os.path.join(self.voice_resources.path[c.TRAIN], \
                                                self.acoustic_feature_filetype)
        label_dir = os.path.join(self.voice_resources.path[c.TRAIN], \
                                                self.input_label_filetype)

        question_file = os.path.join(self.voice_resources.path[c.TRAIN], self.question_file_name)
        
        if not os.path.isfile(question_file):
            sys.exit('Question file doe not exist at %s'%(question_file))

        ## Locate training script and default training config:
        script_dir = self.voice_resources.path[c.ACOUSTIC_MODELLING_SCRIPT]
        config_dir = self.voice_resources.path[c.ACOUSTIC_MODELLING_CONFIG]
        training_script = os.path.join(script_dir, self.acoustic_subrecipe+'.sh')
        default_config = os.path.join(config_dir, self.acoustic_subrecipe + '.cfg')

        ## Specialise the default config with settings made in the voice recipe, then
        ## write to bash config file for use by alignment script:
        train_config_fname = os.path.join(train_location, 'train.cfg')
        train_config = ConfigObj(default_config)
        train_config.update(self.training_settings)

         # get stream definitions from feature extractor too (glotthmm version only)
        #print train_config
        train_config.update(self.stream_definitions)
        #print train_config
        #sys.exit('keswkuvbskdbv')
        write_bash_config(train_config, train_config_fname)


        
        ## Call the training script:
        command = """%s %s %s %s %s %s %s | tee %s/log.txt  \
                    | grep 'Model training'"""%(training_script, \
                            feature_dir, label_dir, question_file, self.hts_dir,\
                            train_location, train_config_fname, train_location)   
        #print command
        success = os.system(command)
        if success != 0:
            sys.exit('AM training failed')
            
        ## Copy the aligner files that need to be preserved:
        final_model_dir = os.path.join(train_location, 'final_model', 'engine')
        ## for SPTK the resulting files will contain: 
        ## duration.pdf logF0.pdf mcep.pdf tree-duration.inf tree-logF0.inf tree-mcep.inf
        for item in os.listdir(final_model_dir):
            shutil.copy(os.path.join(final_model_dir, item), self.model_dir)
        
        #self.load() ## to get new model filenames into self.model's values



class AcousticModelGlott(AcousticModel):


    def process_utterance(self, utt):
        from numpy import loadtxt, savetxt,exp, mean,median
        if utt.has_attribute("waveform"):
            #print "Utt has a natural waveform -- don't synthesise"
            return



        if not self.trained:
            print 'WARNING: Cannot apply processor %s till model is trained'%(self.processor_name)
            return
        
        self.model_dir = os.path.join(self.get_location())
        bin_dir = self.voice_resources.path[c.BIN]
        
        label = utt.get_filename(self.input_label_filetype) 
        owave = utt.get_filename(self.output_filetype)
        
        # generate parameters with hts_engine, one stream at the time
        feats = str.split(self.stream_definitions["STREAM_NAMES"])
        
        self.vuv = 0.4
        for f in feats:
            comm = self.hts_dir + '/hts_engine '
            comm += "  -td %s/tree-duration.inf "%(self.model_dir)
            comm += "  -md %s/duration.pdf "%(self.model_dir)

            comm += "  -tf %s/tree-F0.inf "%(self.model_dir)
            comm += "  -mf %s/F0.pdf "%(self.model_dir)
        
            comm += "  -tm %s/tree-%s.inf "%(self.model_dir, f)
            comm += "  -mm %s/%s.pdf "%(self.model_dir,f)

            comm += "  -ow /tmp/tmp.wav"        
            comm += "  -om /tmp/tmp.%s"%(f)    
            comm += "  -of /tmp/tmp.F0"    
            
            ## windows:
            for stream in ['f', 'm']:
                for winfile in self.winfiles:
                    comm += "  -d%s %s "%(stream, winfile)
            comm += " -b 0.0 " ## for postfiltering 
            comm += "  -u %s "%(self.vuv)
            #comm += "  -ow %s "%(owave)
            comm += "    %s > %s.log"%(label, label)
        
            os.system(comm)

        # process parameters
            
        f0 = []
        for f in reversed(feats):
            os.system(bin_dir+"/x2x +fa /tmp/tmp."+f+" >/tmp/tmp_a."+f)
            if f == "F0":
                f0 = loadtxt('/tmp/tmp_a.F0')
                f0[f0>0]=exp(f0[f0>0])
                f0[f0<=0] = 0
                savetxt("/tmp/tmp_a.f0", f0.astype('float'), fmt = '%.8f')



            if f == "mcep":
                # get orders from acoustic config
                mcep_order = str(29)
                lsf_order =str(30)
                warp = str(0.35)
                os.system(bin_dir+"/freqt -a "+warp+" -A 0.0 -m "+mcep_order+" -M 120 </tmp/tmp.mcep | "+bin_dir+"/c2acr -m 120 -M "+lsf_order+" | "+bin_dir+"/levdur -m "+lsf_order+ " >/tmp/tmp.lpc")
                os.system(bin_dir+"/lpc2lsp -k -m "+lsf_order+" -n 512 -s 16 -p 1 /tmp/tmp.lpc >/tmp/tmp.LSF");
                os.system(bin_dir+"/x2x +fa /tmp/tmp.LSF >/tmp/tmp_a.LSF")

        lsf = loadtxt("/tmp/tmp_a.LSF")

        
        savetxt("/tmp/tmp_a.LSF", lsf.astype('float'), fmt = '%8f')
        # Synthesize 
        conf_dir = self.get_location()+"/../speech_feature_extractor"
        comm = self.voice_resources.path['GLOTT']+"/Synthesis /tmp/tmp_a "+conf_dir+"/main_config.cfg "+conf_dir+"/user_config.cfg"
        os.system(comm)
        os.system("mv /tmp/tmp_a.syn.wav "+owave)
        
   


class AcousticModelWorld(AcousticModel):


    def process_utterance(self, utt):
        from numpy import loadtxt, savetxt,exp, mean,median
        if utt.has_attribute("waveform"):
            #print "Utt has a natural waveform -- don't synthesise"
            return



        if not self.trained:
            print 'WARNING: Cannot apply processor %s till model is trained'%(self.processor_name)
            return
        
        #self.postfilter_coeff = self.postfilter_coeff
        #self.scale_var = self.config.get('scale_var','n')
        #self.speech_rate = float(self.config.get('speech_rate',1.0))
        
        self.model_dir = os.path.join(self.get_location())
        bin_dir = self.voice_resources.path[c.BIN]
        
        label = utt.get_filename(self.input_label_filetype) 
        owave = utt.get_filename(self.output_filetype)
        
        # generate parameters with hts_engine, one stream at the time
        feats = str.split(self.stream_definitions["STREAM_NAMES"])
        
        #self.vuv = 0.4
        for f in feats:
        
            comm = self.hts_dir + '/hts_engine '
            comm += "  -td %s/tree-duration.inf "%(self.model_dir)
            comm += "  -md %s/duration.pdf "%(self.model_dir)

            comm += "  -tf %s/tree-lf0.inf "%(self.model_dir)
            comm += "  -mf %s/lf0.pdf "%(self.model_dir)
        
            comm += "  -tm %s/tree-%s.inf "%(self.model_dir, f)
            comm += "  -mm %s/%s.pdf "%(self.model_dir,f)

            comm += "  -ow /tmp/tmp.wav"        
            comm += "  -om /tmp/tmp.%s"%(f)    
            comm += "  -of /tmp/tmp.lf0"    
            
            ## windows:
            for stream in ['f', 'm']:
                for winfile in self.winfiles:
                    comm += "  -d%s %s "%(stream, winfile)
            comm += " -b %s "%(self.postfilter_coeff) ## for postfiltering 
            comm += " -r %s "%(self.speech_rate) 
            comm += "  -u %s "%(self.vuv)
            #comm += "  -ow %s "%(owave)
            comm += " -ot %s.log "%(label)
            comm += "    %s  "%(label)
        
            print comm
            
            os.system(comm)


        ### hack -- tile silences with pure silence:
        sils = silence_frames_from_trace(label+ '.log')
        
        fftl, ap_dim = get_world_fft_and_apdim(self.sample_rate)

        fz= get_speech('/tmp/tmp.lf0',1)
        mgc= get_speech('/tmp/tmp.mgc',self.speech_coding_config['order']+1) # 40)
        ap= get_speech('/tmp/tmp.bap',ap_dim)

        for (i,val) in enumerate(sils):
            if val == 1:
                mgc[i,:] = 0.0
                fz[i] = -1.0
                ap[i] = 0.0
        
        ##
        #ap = np.zeros(np.shape(ap))
                
                
        # var sscale:
        if self.scale_var != 1.0:
           mgc = scale_variance(mgc, scale_factor=self.scale_var)


        ap =np.zeros(np.shape(ap))
        put_speech(fz, '/tmp/tmp.lf0')
        put_speech(mgc, '/tmp/tmp.mgc')
        put_speech(ap, '/tmp/tmp.bap') 

        # process parameters -- OSW todo wavesynth processor sharing config with extraction
            
        f0 = []
        for f in reversed(feats):
        
            if f == "lf0":
                os.system(bin_dir+"/x2x +fa /tmp/tmp."+f+" >/tmp/tmp_a."+f)
                
                f0 = loadtxt('/tmp/tmp_a.lf0')
                f0[f0>0]=exp(f0[f0>0])
                f0[f0<=0] = 0
                savetxt("/tmp/tmp_a.f0", f0.astype('float'), fmt = '%.8f')        
        
                os.system(bin_dir+"/x2x +ad /tmp/tmp_a.f0 > /tmp/tmp_a.f0.d")
        
            else:
                os.system(bin_dir+"/x2x +fd /tmp/tmp."+f+" >/tmp/tmp_d."+f)
            
        


        bin = self.hts_dir  ## world here too
        
        
        alpha = self.alpha
        order = self.mcep_order
        sr = self.sample_rate



        '''
        alpha = 0.77
        order = 59
        fftl = 2048
        sr = 48000
        '''

        
        #print 'h1'
        comm = "%s/mgc2sp -a %s -g 0 -m %s -l %s -o 2 /tmp/tmp.mgc | %s/sopr -d 32768.0 -P | %s/x2x +fd -o > /tmp/tmp.spec"%(bin, alpha, order, fftl, bin, bin)
        #comm = "%s/mgc2sp -a %s -g 0 -m %s -l %s -o 2 /tmp/tmp.mgc | %s/sopr -d 32768.0 -P > /tmp/tmp.spec"%(bin, alpha, order, fftl, bin, bin)
        os.system(comm)
    
        '''Avoid:   x2x : error: input data is over the range of type 'double'!
               -o      : clip by minimum and maximum of output data            
                 type if input data is over the range of               
                 output data type.
        '''    
    
    


        comm = "%s/synth %s %s /tmp/tmp_a.f0.d /tmp/tmp.spec /tmp/tmp_d.bap /tmp/tmp.resyn.wav"%(bin, fftl, sr)
        print comm
        os.system(comm)
        os.system("mv /tmp/tmp.resyn.wav "+owave)
    
    
 
 
 
 


class HTSDurationModel(AcousticModel):


    def process_utterance(self, utt):
        if utt.has_attribute("waveform"):
            #print "Utt has a natural waveform -- don't synthesise"
            return

        if not self.trained:
            print 'WARNING: Cannot apply processor %s till model is trained'%(self.processor_name)
            return
        
        self.postfilter_coeff = self.config.get('postfilter_coeff','0.0')
        self.scale_var = self.config.get('scale_var','n')
        self.speech_rate = float(self.config.get('speech_rate',1.0))
        
        self.model_dir = os.path.join(self.get_location())
        bin_dir = self.voice_resources.path[c.BIN]
        
        label = utt.get_filename(self.input_label_filetype) 
        
        # generate parameters with hts_engine, one stream at the time
        feats = str.split(self.stream_definitions["STREAM_NAMES"])
        
        ## choose arbitrary stream -- just want durations!:--
        f = feats[0]
        
        self.vuv = 0.4
        
    
        comm = self.hts_dir + '/hts_engine '
        comm += "  -td %s/tree-duration.inf "%(self.model_dir)
        comm += "  -md %s/duration.pdf "%(self.model_dir)

        comm += "  -tf %s/tree-lf0.inf "%(self.model_dir)
        comm += "  -mf %s/lf0.pdf "%(self.model_dir)
    
        comm += "  -tm %s/tree-%s.inf "%(self.model_dir, f)
        comm += "  -mm %s/%s.pdf "%(self.model_dir,f)

        comm += "  -ow /tmp/tmp.wav"        
        comm += "  -om /tmp/tmp.%s"%(f)    
        comm += "  -of /tmp/tmp.lf0"    
        
        ## windows:
        for stream in ['f', 'm']:
            for winfile in self.winfiles:
                comm += "  -d%s %s "%(stream, winfile)
        comm += " -b %s "%(self.postfilter_coeff) ## for postfiltering 
        comm += " -r %s "%(self.speech_rate) 
        comm += "  -u %s "%(self.vuv)
        #comm += "  -ow %s "%(owave)
        comm += " -ot %s.log "%(label)
        comm += "    %s  "%(label)
    
        print comm
        
        os.system(comm)


        ### 
        durations = state_durations_from_trace(label+ '.log')
         

        self.ms_framerate = 5 ## hardcoded
        self.child_tag = 'state'
        self.target_nodes = '//segment'
        
        
        ### this code from NN.py (to refactor):--         
         
        m,n = numpy.shape(durations)
        nodes = utt.xpath(self.target_nodes)
        assert  m == len(nodes)
        
        start = 0
        for (node, state_durs) in zip(nodes, durations):
            for dur in state_durs:
                end = start + dur
                child = Element(self.child_tag)
                child.set('start', str(start * self.ms_framerate))
                child.set('end', str(end * self.ms_framerate))
                node.add_child(child)
                
                start = end         
  
    
def scale_variance(speech, scale_factor=1.0):
    utt_mean = numpy.mean(speech, axis=0) 
    utt_std =  numpy.std(speech, axis=0) 

    std_scale = numpy.ones(numpy.shape(utt_std)) * scale_factor

    nframes, ndim = numpy.shape(speech)
    utt_mean_matrix = numpy.tile(utt_mean, (nframes,1))
    std_scale_matrix = numpy.tile(std_scale, (nframes,1))

    scaled_speech = ((speech - utt_mean_matrix) * std_scale_matrix) + utt_mean_matrix
    return scaled_speech


                    
        
def silence_frames_from_trace(fname):
    lines = readlist(fname)
    phones = [l for l in lines if 'Name' in l]
    phones = [l.split('-')[2].split('+')[0] for l in phones]
   
    
    frames = [l for l in lines if '(frames)' in l]
    frames = [int(re.findall('\d+',l)[0]) for l in frames ][1:]
    
    
    nframes =sum(frames)
    
    assert len(phones) == len(frames)/5
    
    pairs = []
    p = 0
    s = 0
    while s < len(frames):
        for i in range(5):
            pairs.append((phones[p], frames[s]))
            s += 1
        p += 1
    

    
    frames = np.zeros(nframes,dtype=int)
    i= 0
    for (p,length) in pairs:
        for j in range(length):
            if p in ['_END_','sil']:
                frames[i] = 1.0
            i +=1
    
    return frames
    
def state_durations_from_trace(fname):
    lines = readlist(fname)

    phones = [l for l in lines if 'Name' in l]
    phones = [l.split('-')[2].split('+')[0] for l in phones]
   
    
    frames = [l for l in lines if '(frames)' in l]
    frames = [int(re.findall('\d+',l)[0]) for l in frames ][1:]

    
    nframes =sum(frames)
    
    assert len(phones) == len(frames)/5
    
    pairs = []
    p = 0
    s = 0
    outdata = []
    while s < len(frames):
        statelist = []
        for i in range(5):
            statelist.append(frames[s])
            s += 1
        outdata.append(statelist)
        p += 1
    
    return numpy.array(outdata)
        