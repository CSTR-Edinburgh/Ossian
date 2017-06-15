#!/usr/bin/env python


'''

'''

import sys
import glob
import os
from lxml import etree
from argparse import ArgumentParser

def main_work():

    #################################################
      
    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-i', dest='indir', required=True)
#     a.add_argument('-x', dest='token_xpath', required=True, \
#                     help= "XPath expression to match nodes (tokens) of right type")
#     a.add_argument('-o', dest='outdir', required=True, \
#                     help= "Put output here: make it if it doesn't exist")
#     a.add_argument('-n', dest='token_name', default="word", \
#                     help= "Attribute added to nodes will be called <TOKEN_NAME>_index")
    opts = a.parse_args()
    
    # ===============================================
#     outdir = opts.outdir
    indir = opts.indir
#     token_xpath = opts.token_xpath
#     attrib_name = opts.token_name + '_index'
    # ===============================================


#     if not os.path.isdir(outdir):
#         os.makedirs(outdir)

#     i = 1
#    token_xpath = "//token[@token_class='word']"
    token_xpath = "//token"
  
  
    print 
    print 'syllable'
  
    for uttfile in sorted(glob.glob(indir + '/*.utt')):
        
#         words = []
#         sylls = []
#         utt = etree.parse(uttfile)
#         #print utt
#         #print  utt.xpath(token_xpath)
#         for node in utt.xpath(token_xpath):
#             if 'prom' in node.attrib:
#                 words.append( node.attrib['norm_text'] + '_' + node.attrib['prom'])
#             else:
#                 words.append( node.attrib['norm_text'] )
#             for syll in node.xpath('.//syllable'):
#                 
#         print ' '.join(words).replace('  ', ' ')
# 


        words = []
        sylls = []
        utt = etree.parse(uttfile)
        #print utt
        #print  utt.xpath(token_xpath)
        for node in utt.xpath(token_xpath):
            
            syllprom = [syll.attrib['prom'] for syll in node.xpath('.//syllable')]
            
            syllprom = '-'.join(syllprom)
                    
            words.append( node.attrib['norm_text'] + '_' + syllprom)
    
                
        print ' '.join(words).replace('  ', ' ')


    print '\n\n\n\n\n-------dynamic_prom on syll\n\n\n\n'
  
    for uttfile in sorted(glob.glob(indir + '/*.utt')):
      

        words = []
        sylls = []
        utt = etree.parse(uttfile)
        #print utt
        #print  utt.xpath(token_xpath)
        for node in utt.xpath(token_xpath):
            
            syllprom = [syll.attrib['dynamic_prom'] for syll in node.xpath('.//syllable')]
            
            syllprom = '-'.join(syllprom)
                    
            words.append( node.attrib['norm_text'] + '_' + syllprom)
    
                
        print ' '.join(words).replace('  ', ' ')


    print '\n\n\n\n\n-------words:\n\n\n\n'
  
    for uttfile in sorted(glob.glob(indir + '/*.utt')):
        
        words = []
        utt = etree.parse(uttfile)
        #print utt
        #print  utt.xpath(token_xpath)
        for node in utt.xpath(token_xpath):
            if 'prom' in node.attrib:
                words.append( node.attrib['norm_text'] + '_' + node.attrib['prom'])
            else:
                words.append( node.attrib['norm_text'] )
           
                
        print ' '.join(words).replace('  ', ' ')




if __name__=="__main__":

    main_work()
