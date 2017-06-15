#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import struct
import numpy
from numpy import array, reshape, shape
from scipy.interpolate import splev, splrep


def extract_portion_and_write(infile, outfile, old_dim, new_dim_start, new_dim_width, remove_htk_header):

    new_data = extract_portion(infile, old_dim, new_dim_start, new_dim_width, remove_htk_header)
    put_speech(new_data, outfile)

def extract_portion(infile, old_dim, new_dim_start, new_dim_width, remove_htk_header):

    assert new_dim_start >= 1
    new_dim_start -= 1
    new_dim_stop = new_dim_start + new_dim_width

    data = get_speech(infile, old_dim, remove_htk_header=remove_htk_header)
    new_data = data[:, new_dim_start : new_dim_stop]
    
    return new_data


def get_speech(infile, dim, remove_htk_header=False):

    data = read_floats(infile)
    if remove_htk_header:
        data = data[3:]  ## 3 floats correspond to 12 byte htk header

    assert len(data) % float(dim) == 0,"Bad dimension!"
    m = len(data) / dim
    data = array(data).reshape((m,dim))
    return data

def put_speech(data, outfile):
    m,n = shape(data)
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



def spline_smooth_fzero(traj, trim_n_frames=4, s=100, k=1):

    ## set unvoiced to 0 in case we are using log f0:
    traj = numpy.maximum(traj, 0.0)

    ## remove starts of voiced regions to exclude obstruent peturbations:
    for i in range(trim_n_frames):
        voiced_ix = numpy.nonzero(traj)[0] ## returns tuple for each dimension of input -- take the first
        for ix in voiced_ix:
            if ix-1 not in voiced_ix:
                traj[ix] = 0
        ## reverse order pass -- ends of voiced regions:
        for ix in reversed(voiced_ix):
            if ix+1 not in voiced_ix:
                traj[ix] = 0
      
    ## 1) add values at ends
    voiced_ix = numpy.nonzero(traj)[0] ## returns tuple for each dimension of input -- take the first
    voiced = traj[voiced_ix]
    if numpy.prod(numpy.shape(voiced)) == 0: ## i.e. if all unvoiced
        mini = 0.001   ## special value for all unvoiced, must be > 0 or else gets stripped below!
        first_v = 1
        last_v = -1
    else:
        mini=numpy.min(voiced)
        first_v = voiced_ix[0]
        last_v = voiced_ix[-1]
    
    traj[:first_v] = mini
    traj[last_v:]= mini
 
    ## 2) rerun
    voiced_ix = numpy.nonzero(traj)[0] ## returns tuple for each dimension of input -- take the first
    voiced = traj[voiced_ix]
    
    tck = splrep(voiced_ix, voiced, s=s, k=k)  
    ## k = order of the spline fit (3->cubic)
    ## higher s = smoother, 0 = interpolation

    x2 = range(len(traj))
    y2 = splev(x2, tck)

    return y2


