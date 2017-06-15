#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Project: Natural Speech Technology - February 2015 - www.natural-speech-technology.org
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk
  
import sys
import os
import struct
import glob
import numpy
from numpy import array
from argparse import ArgumentParser


def main_work():

    #################################################
      
    # ======== Get stuff from command line ==========

    a = ArgumentParser()
    a.add_argument('-cmp', dest='cmpdir', required=True)
    a.add_argument('-out', dest='outdir', required=True, \
                    help= "Put output here: make it if it doesn't exist")
    a.add_argument('-streams', default='LSF,LSFsource,HNR,Gain,F0')
    a.add_argument('-widths', default='30,10,5,1,1')
    a.add_argument('-deltas', default=3, type=int, \
                            help='e.g. 3 for static + delta + deltadelta')                
    opts = a.parse_args()
    
    # ===============================================    
    streams = opts.streams.split(',')
    widths = [int(val) for val in opts.widths.split(',')]
    
    assert len(streams) == len(widths)
    
    # ===============================================
    streams_out = [os.path.join(opts.outdir, stream) for stream in streams]    

    for direc in [opts.outdir] + streams_out:
        if not os.path.isdir(direc):
            os.makedirs(direc)

    total_dim = sum(widths) * opts.deltas


    for cmp in glob.glob(os.path.join(opts.cmpdir, '*.cmp')):
        junkpath,base=os.path.split(cmp)
        base=base.replace('.cmp','')
        data = get_speech(cmp, total_dim, remove_htk_header=True)
        start = 0
        #print '========'
        print base 
        for (stream, width) in zip(streams, widths):
            #print '   ' + stream
            outfile = os.path.join(opts.outdir, stream, base + '.' + stream)
            end = start + width
            stream_data = data[:, start:end]
            put_speech(stream_data, outfile)
            start = start + (width * opts.deltas)
            
        
        

def get_speech(infile, dim, remove_htk_header=False):

    data = read_floats(infile)
    if remove_htk_header:
        data = data[3:]  ## 3 floats correspond to 12 byte htk header

    assert len(data) % float(dim) == 0,"Bad dimension!"
    m = len(data) / dim
    data = array(data).reshape((m,dim))
    return data

def put_speech(data, outfile):
    m,n = numpy.shape(data)
    size = m*n
    flat_data = list(data.reshape((size, 1)))
    write_floats(flat_data, outfile)

def write_floats(data, outfile):
    m = len(data)             
    format = str(m)+"f"

    packed = struct.pack(format, *data)
    f = open(outfile, "w")
    f.write(packed)
    f.close()

def read_floats(infile):
    f = open(infile, "r")
    l = os.stat(infile)[6]  # length in bytes
    data = f.read(l)        # = read until bytes run out (l)
    f.close()

    m = l / 4               
    format = str(m)+"f"

    unpacked = struct.unpack(format, data)
    unpacked = list(unpacked)
    return unpacked


if __name__=="__main__":

    main_work()

