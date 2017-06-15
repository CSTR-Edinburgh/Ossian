#!/usr/bin/env python
##
## Project: Simple4All - November 2013 - www.simple4all.org 
## Contact: Oliver Watts - owatts@staffmail.ed.ac.uk


import sys
import re
from configobj import ConfigObj

## History: public HTS -> Junichi's script -> Reima made stream independent -> Oliver
## put in separate script and moved from perl to python

# sub routine for generating proto-type model (Copy from HTS-2.1)

# Made stream-independent 23/4/2012 rk


proto_out = sys.argv[1]
config_in = sys.argv[2]


config = ConfigObj(config_in)

static_stream_sizes = config.get('STATIC_STREAM_SIZES', default='25 1 1 1')  ### defaults for SPTK
MSD_stream_info = config.get('MSD_STREAM_INFO', default='0 1 1 1') 
stream_weights = config.get('STREAM_WEIGHTS', default='1.0 1.0 1.0 0.9') 

#static_stream_sizes = config.get('static_stream_sizes', default='25 1 1 1')  ### defaults for SPTK
#MSD_stream_info = config.get('MSD_stream_info', default='0 1 1 1') 
#stream_weights = config.get('stream_weights', default='1.0 1.0 1.0 0.9') 


NSTATE = 1 ## fixed for skip model


## string -> numeric list conversion:
def int_list(string):
    seq = re.split('\s+', string.strip())
    return [int(item) for item in seq]
    
static_stream_sizes = int_list(static_stream_sizes)
MSD_stream_info = int_list(MSD_stream_info)



n_weights = len(re.split('\s+', stream_weights.strip()))
num_stream = len(static_stream_sizes)
if (len(MSD_stream_info) != num_stream) or (n_weights!= num_stream):
    sys.exit('stream info not same: %s %s %s'%(static_stream_sizes, MSD_stream_info, stream_weights))


stream_indexes = range(1, num_stream+1)



total_stream_sizes = []
for (MSD,size) in zip(MSD_stream_info, static_stream_sizes): 
   if MSD:
        total_stream_sizes.append(size)
   else:
        total_stream_sizes.append(size * 3)

vsize = sum(total_stream_sizes)


            

d = ''

## ----- HEADER -----
d += '~o <VecSize> %s <USER> <DIAGC> '%(vsize)

d += '<MSDInfo> %s '%(num_stream)
d += ' '.join([str(val) for val in MSD_stream_info])
d += '\n'

d += '<StreamInfo> %s '%(num_stream)
d += ' '.join([str(val) for val in total_stream_sizes])
d += '\n'

## ----- output HMMs ------
d += "<BeginHMM>\n"
d += "  <NumStates> %d\n"%(NSTATE+2)

# output HMM states 
for i in range(2, NSTATE+2):

    # output state information
    d += "  <State> %s\n"%(i)

    # output stream weight
    d += '  <SWeights> %d '%(num_stream)

    d += stream_weights
    d += '\n'


    for (i, MSD, size) in zip(stream_indexes, MSD_stream_info, total_stream_sizes):
        d += "  <Stream> %d\n"%(i)

        if not MSD:
            d += "    <Mean> %d\n      "%(size)
            for j in range(size):
                d += "0.0 "
            d += '\n'
      
            d += "    <Variance> %d\n      "%(size)
            for j in range(size):
                d += "1.0 "
            d += '\n'
                      
        else:
        
            d += "  <NumMixes> 2\n"
            
            # output 1st space (non 0-dimensional space)
            d += "  <Mixture> 1 0.5000\n"
            d += "    <Mean> 1 0.0 \n"
            d += "    <Variance> 1 1.0 \n"	      
      
            # output 2nd space (0-dimensional space)
            d += "  <Mixture> 2 0.5000\n"
            d += "    <Mean> 0 \n"
            d += "    <Variance> 0 \n"	 


# output state transition matrix
d +=  '<TransP> %d\n'%(NSTATE+2)
d +=  "    0.0 0.0 1.0 \n"
d +=  "    0.0 0.5 0.5 \n"
d +=  "    0.0 0.0 0.0 \n"
d += "\n<EndHMM>\n"

f = open(proto_out, 'w')
for line in d:
    f.write(line)
f.close()


