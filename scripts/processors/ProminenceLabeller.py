#!/usr/bin/env python
# -*- coding: utf-8 -*-



import numpy as np
import os.path

from UtteranceProcessor import *
from scipy import signal

from collections import OrderedDict, defaultdict
import util.acoustic_feats as ac
import util.Wavelets as cwt
import util.cwt_utils


from naive.naive_util import config_list as clist
from naive.naive_util import str2bool

### osw: unused import of old package? :--
## import util.loma



CWT_DEBUG = 1
if CWT_DEBUG:
    import matplotlib
    try:
        matplotlib.use('macosx')
    except:
        pass
    import pylab

class ProminenceLabeller(UtteranceProcessor):


    def load(self):
        
        self.output_attribute = self.config.get('output_attribute', 'prom')
        self.feats = clist(self.config.get('features', ["F0", "Gain","dur"]))
        self.prom_weights = clist(self.config.get('prom_weights', [0.4, 0.4, 0.2]))
        self.param_dir = self.config.get('param_dir', 'acoustic')
        self.frame_len = self.config.get('frame_length', 5)
        self.level = self.config.get('level','//token[@token_class=\"word\"]')
        self.scale_distance = float(self.config.get('scale_distance',0.5))
        self.num_octaves = int(self.config.get('num_octaves', 12))

        self.wscale = 10     ## this is set in training 
        self.variances = {}  ## this is set in training 
            
        if CWT_DEBUG:
            pylab.ion()

        self.fzero_feat = ''
        for f in self.feats:
            if 'f0' in f.lower():
                self.fzero_feat = f
        assert self.fzero_feat != '', 'ProminenceLabeller needs a feature containing f0!'
                
        self.dynamic_size_wavelet = str2bool(self.config.get('dynamic_size_wavelet', 'no'))
        
        self.use_stress_track = str2bool(self.config.get('use_stress_track', 'no'))
        self.stress_xpath = self.config.get('stress_xpath', '//syllable[@stress="stress_1"]')
        
        ## for plotting/debugging:-
        self.text_attribute = self.config.get('text_attribute', 'text')
        
        
    def _get_durations(self, utt, level):
        
        tokens = utt.xpath(level) 
        assert tokens != [], 'Xpath %s does not match any nodes!'%(level)
        
        w_times = []
       
        for i in range(len(tokens)):
            if tokens[i].get("start"):
                st = int(tokens[i].get("start"))/int(self.frame_len)
                end = int(tokens[i].get("end"))/int(self.frame_len)
                w_times.append([st, end, tokens[i].get(self.text_attribute)])
        return w_times
    
    
    def _process_acoustic_feats(self,utt):
     
        feats = OrderedDict()
        for f in self.feats:
            if f=='dur':

                #feats[f] = ac.duration(self._get_durations(utt, self.level))
                feats[f] = ac.duration(self._get_durations(utt, self.level))
                
            else:
                feat_dir = self.voice_resources.get_filename(self.param_dir, c.TRAIN)
                fname=feat_dir+"/"+utt.get("utterance_name")+"."+f
                if not os.path.isfile(fname):
                    print "acoustic feature file "+fname+" not found"
                    sys.exit(1)
                    
                feat_type = f
                if 'f0' in f.lower():
                    feat_type = 'f0'
                    
                feats[f] = ac.process(fname, feat_type)
     
        return feats
    
    
    def _get_stress_track(self, utt, low_val=0.5):    
        
        stressed_ix = []
        for stressed_part in utt.xpath(self.stress_xpath):
            start = int(stressed_part.get('start')) / self.frame_len
            end = int(stressed_part.get('end')) / self.frame_len
            stressed_ix.extend(range(start, end))
    
        nframes = int(utt.get('end')) / self.frame_len
        stressed_frames = np.ones(nframes) * low_val
        stressed_frames[stressed_ix] = 1.0
        
        ## slightly smooth the track w 100ms Hamming window:
        stressed_frames = ac._smooth(stressed_frames, int(100.0/self.frame_len), type="HAMMING")
        return stressed_frames
        
        
    def process_utterance(self, utt):

        ## Only apply in training, where an utterance has a waveform / audio:
        if not (utt.has_external_data("wav") or utt.has_external_data("cmp")):
            return
        
        # load and process acoustic features
        feats = self._process_acoustic_feats(utt)
        
        for f in feats:
            feats[f] = util.cwt_utils.normalize(feats[f],self.variances[f])


        # duration energy integration more usable than raw duration
#         if 'dur' in feats:
#             feats['dur'] = (feats['dur']+feats['Gain'][:len(feats['dur'])])/2.0
#        
        word_nodes = utt.xpath(self.level)
        assert word_nodes != [], 'Xpath %s does not match any nodes!'%(self.level)
        words = self._get_durations(utt,self.level)
      
                    
        # capetown wavelet package setup
        s0 = 2 # first scale in number of frames
        dj = self.scale_distance # distance of bands in octaves
        J =  self.num_octaves #number of octaves
        maxscale = len(feats[self.fzero_feat])/(2.0**J) #maximum scale defined as proportion of the signal
                



        if CWT_DEBUG:
            pylab.clf()
            for f in feats:
                pylab.plot(feats[f], label=f)
                util.cwt_utils.plot_labels(words,shift=-3)
            raw_input()
            pylab.clf()

        # perform wavelet transform, select appropriate scale and calculate peak heights            
        prominences = {}
        
        
        if self.dynamic_size_wavelet:
        
            seg_length_sum = 0
            segs = utt.xpath(self.level)
            assert segs != [], 'Xpath %s does not match any nodes!'%(self.level)
            seg_count = len(segs)
            for w in segs:
                seg_length_sum+=(float(w.get("end"))-float(w.get("start")))/int(self.frame_len)
            
            mean_seg_length = seg_length_sum/seg_count
            #perform dummy wavelet transform to determine scale closest to average word duation
            maxscale = (1000/(2.0**10))
            scales=cwt.MexicanHat(np.zeros(1000),maxscale,int(1/self.scale_distance),scaling="log").scales*2
            scale_to_use =  np.abs(scales-mean_seg_length).argmin()-1
        else:
            scale_to_use = self.wscale
    
        i = 1
        for f in feats:
            # perform wavelet transform
            wavelet_matrix = cwt.MexicanHat(feats[f],maxscale,int(1/self.scale_distance),scaling="log")
            wavelet_matrix = util.cwt_utils.scale_for_reconstruction(wavelet_matrix.getdata(), dj,s0)



            # get peaks from word scale
            #prom_param = util.cwt_utils.normalize(wavelet_matrix[wscale].astype(float))
            prom_param = wavelet_matrix[scale_to_use].astype(float)
            
            
            prominences[f] = util.cwt_utils.calc_prominence(prom_param, words, np.max, use_peaks=True)

            if CWT_DEBUG:
               
                pylab.ylim(0, 7) # -5,20)
                pylab.title(f)
                pylab.plot(feats[f]+i*3, label="orig",color='gray')
                pylab.plot(prom_param+i*3, label=f,color='red')
                util.cwt_utils.plot_labels(words)
                util.cwt_utils.plot_prom_labels(words, prominences[f],shift=i)
                #os.system("afplay %s" %utt.get("waveform"))
               
            if self.use_stress_track:
                stress_track = self._get_stress_track(utt)
                
                weighted_track = prom_param * stress_track
                
                if CWT_DEBUG:
                    pylab.plot(stress_track + i*4, label="stress",color='green')
                    
                    pylab.plot(weighted_track + i*4,color='blue', label='weighted by stress')            
            
           
            i= i + 1
        if CWT_DEBUG:
            raw_input()
        # combine measurements and add prominence attribute to words
            
        for i in range(len(words)):
        
            prominence = 0
            feat_i = 0
            for f in feats:
                prominence+=prominences[f][i]*float(self.prom_weights[feat_i])*1.2
                feat_i+=1
            if prominence >3:
                prominence = 3
            if prominence < 0:
                prominence = 0
            # quantization for HTS decision trees, for DNNs, do not round

            word_nodes[i].set(self.output_attribute, str(int(round(prominence))))
            # print word_nodes[i].get("text"), word_nodes[i].get("prom")
            

        
    def do_training(self, speech_corpus, text_corpus):
        
        # fix word scale based on average word duration in corpus
        word_length_sum = 0
        word_count = 0
        for utt in speech_corpus:
           
            words = utt.xpath(self.level)
            assert words != [], 'Xpath %s does not match any nodes!'%(self.level)
            word_count+=len(words)
            for w in words:
                word_length_sum+=(float(w.get("end"))-float(w.get("start")))/int(self.frame_len)
                
        mean_word_length = word_length_sum/word_count
        #perform dummy wavelet transform to determine scale closest to average word duation
        maxscale = (1000/(2.0**10))
        scales=cwt.MexicanHat(np.zeros(1000),maxscale,int(1/self.scale_distance),scaling="log").scales*2
        self.wscale =  np.abs(scales-mean_word_length).argmin()-1


        # get variance of acoustic features
        # should get wscale variane as well
        max_utt = 100
        utt_i = 0
        self.variances =defaultdict(float)
        self.word_variances =defaultdict(float)
        for utt in speech_corpus:
            if utt_i == max_utt:
                break
            feats = self._process_acoustic_feats(utt)
            for f in self.feats:
                self.variances[f] += np.std(feats[f])
            
            utt_i+=1

        for f in self.feats:
            self.variances[f] /= utt_i
        
        print self.variances
        
