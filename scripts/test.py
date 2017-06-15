#!/usr/bin/env python

from naive.naive_util import *
import glob
from util.speech_manip import get_speech

from main.Utterance import *


# for f in glob.glob('/Users/owatts/repos/simple4all/TASSAL/branches/cleaner_june_2013/train/en/speakers/tundra_1hour/baseline05/cmp/livingalone_*.cmp'):
#     print f + " " + str(get_htk_filelength(f))
#     

## Wavelets

if False:
    from processors import NN

    import numpy as np
    # track = np.array([0,0,0,0,1,1,1,1,0,0,1,1,1,0,0,0,0,0])
    # print track
    # print NN.fill_short_unvoiced_gaps(track, 2)


    fzero = get_speech('/tmp/tmp.lf0' , 1)

    print np.shape(fzero)

    import pylab

    fzero = fzero[:,0]

    fzero = np.maximum(fzero, 50)


    recon = NN.wavelet_manipulation(fzero, [1]*22)


    pylab.subplot('211')
    pylab.plot(fzero)


    pylab.subplot('212')
    pylab.plot(recon)
    # 
    # 
    # pylab.subplot('513')
    # pylab.plot(scales[:,5])
    # 
    # 
    # pylab.subplot('514')
    # pylab.plot(scales[:,10])
    # 
    # 
    # pylab.subplot('515')
    # 
    # pylab.plot(recon)
    pylab.show()
    
    






### utt audio access:
if False:
    import numpy
    utt = Utterance('/afs/inf.ed.ac.uk/group/cstr/projects/blizzard_entries/blizzard2016/tool/Ossian/train/en/speakers/fls_2016_segmented_TOY/english_blizz16_02_prom_annotation/utt/AMidsummerNightsDream_000.utt')

    print utt
    utt.pretty_print()
    
    print [utt.get('acoustic_stream_names')    ]
    print '-----'
    for (word_i,word) in enumerate(utt.xpath('//token[@token_class="word"]')):
        print word.get('norm_text')
        d = utt.get_acoustic_features(word, 'lf0')
        i = utt.get_acoustic_features(word, 'lf0', interpolate_fzero=True)
        m = utt.get_acoustic_statistics(word, 'mgc', dim=0)
        s = utt.get_acoustic_statistics(word, 'mgc')
        l = utt.get_acoustic_statistics(utt, 'lf0', interpolate_fzero=True)

        print d
        print l
        #print i
        utt.get_waveform_segment(word, '/Users/owatts/temp/word_%s.wav'%(word_i))
        
        print 
        
    
    u = Utterance('/afs/inf.ed.ac.uk/group/cstr/projects/blizzard_entries/blizzard2016/tool/Ossian/train/en/speakers/fls_2016_segmented_TOY/english_blizz16_02_prom_annotation/utt/AMidsummerNightsDream_000.utt')
    u.pretty_print()
    u.enrich_with_acoustic_statistics('//token[@token_class="word"]', [('lf0', 0), ('mgc',0), ('mgc',1)])
    u.pretty_print()
    
    
if False:
    for uttname in glob.glob('/afs/inf.ed.ac.uk/group/cstr/projects/blizzard_entries/blizzard2016/tool/Ossian/train/en/speakers/fls_2016_segmented_TOY/english_blizz16_02_prom_annotation/utt/AMidsummerNightsDream_*.utt') :
    
        utt = Utterance(uttname)
        print 
        print '--------------'
        print 
        for token in utt.xpath('//token'):

            text = token.get('norm_text')
            silence = ''
            if len(token.xpath('.//segment[@pronunciation="sil"]')) > 0:
                silence = 'SIL!!!'
            if 'rf_class_break_annot' in token.attrib:
                print text + '   ' + token.attrib['rf_class_break_annot'] + ' ' + token.attrib['rf_regress_break_annot'] + ' ' + silence
            else:
                print text


if True:
        import subprocess, unicodedata
        word = 'lysander'
        comm = "export PYTHONPATH=/Users/owatts/repos/ossian_git_test/Ossian/tools/bin/../lib/python2.7/site-packages:/Users/owatts/repos/ossian_git_test/Ossian/tools/bin/../g2p ;  echo 'lysander' | /Users/owatts/repos/ossian_git_test/Ossian/tools/bin/g2p.py  --model /afs/inf.ed.ac.uk/group/cstr/projects/blizzard_entries/blizzard2016/tool/Ossian/voices//en/fls_2016_segmented_TOY_50/english_blizz16_safe_monophone/processors/lexicon_lookup/lts.model --variants-number 6 --apply -"
        pronun = subprocess.check_output(comm, shell=True, stderr=subprocess.STDOUT)
        if 'failed to convert' in pronun:
            print comm
            print 'WARNING: couldnt run LTS for %s'%(word)
            
        
        ## remove the 'stack usage' output line -- its position varies:
        pronun = unicodedata.normalize('NFKD', pronun.decode('utf-8')) 
                            ## ^----- 2015-11-4: moved this line back from c.440 
                            
        pronun = pronun.strip(' \n').split('\n')
        print pronun
        
        ## deal with this, but TODO: work out long-term solution --
        assert len(pronun) >= 2,str(pronun)     ## ==   -->   >=     to handle extra warnings
        if type(word) == str:
            word = word.decode('utf-8')
        normalised_word = unicodedata.normalize('NFKD', word) 
        real_pronuns = []
        for line in pronun:
            if 'stack usage' not in line and normalised_word in line:   ## word in line   added to reject warnings
                real_pronuns.append(line)
        
        word = unicodedata.normalize('NFKD', word)  
        clean_pronuns = []      
        for line in  real_pronuns:
            (outword, number, score, pronun) = re.split('\s+', line, maxsplit=3)
            outword = unicodedata.normalize('NFKD', outword.decode('utf-8'))
            if type(word) == str:
                word = word.decode('utf-8')
            assert outword == word,'don\'t match: %s and %s'%(outword, word)
                        ## sequitur seems to return decomposed forms 


            clean_pronuns.append(pronun)
        clean_pronuns = ' sil '.join(clean_pronuns)
        return clean_pronuns