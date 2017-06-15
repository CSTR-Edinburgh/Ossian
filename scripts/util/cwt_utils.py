
#import matplotlib
#matplotlib.use('macosx') 
import numpy as np

#from matplotlib import pyplot as pylab
#import pylab

## osw: unused import of old package? :--
#import cwt as wavelet



def plot_labels(labels,shift = 0,  fig="", text = True):
    import pylab
    if fig == "":
        fig = pylab
    #print labels
    for (start, end,token) in labels: 
            

        if token:
                
            fig.axvline(x=start, color='black')
            fig.axvline(x=end, color='black')
            if text:
                fig.text(start+1-shift,0, token) #, color="grey")
            fig.legend()


def plot_prom_labels(labels, prominences, shift = 0,fig=""):
    import pylab
    if fig == "":
        fig = pylab
    for i in range(len(labels)):
        (start, end, token) = labels[i]
        if token and i <=len(prominences):
            fig.text(start+3, shift, (round(prominences[i],1)))
    
    
        pass

def get_peaks(params):
    #peaks = []
    indices = []

    
    zc = np.where(np.diff(np.sign(np.diff(params))))[0]
    
    indices = (np.diff(np.sign(np.diff(params))) < 0).nonzero()[0] +1
    
    peaks = params[indices]
    return np.array([peaks, indices])

def get_valleys(params):
    return get_peaks(-params)

def get_best_scale(wavelet_matrix, num_units):
    best_i = 0
    best = 999
    for i in range(0, wavelet_matrix.shape[0]):
        num_peaks = len(get_peaks(wavelet_matrix[i])[0])
        dist= abs(num_peaks - num_units)
        if dist < best:
            best = dist
            best_i = i

    return best_i
                         
def normalize(params, std=0):
    if std ==0:
        std = np.std(params)

    mean = np.mean(params)
    return (params - mean) / std

def unnormalize(params, mean, std):
    return  mean + (params - np.mean(params))*(std/(np.std(params)))





def scale_for_reconstruction(wavelet_matrix, scale_dist=1.0, s0=3):
    scaled = np.array(wavelet_matrix)

    for i in range(0, wavelet_matrix.shape[0]):
        scaled[i] *= 2**(-(i+s0-1)*scale_dist/2)
      
    return scaled




def calc_prominence(params, labels, func=np.max, use_peaks = True):
    labelled = []
    norm = params.astype(float)
    for (start, end, word) in labels:
   
        if end -start == 0:
            continue
        #print start, end, word
        if use_peaks:
            peaks = []
            #pylab.clf()
            #pylab.plot(params[start:end])

            (peaks, indices)=get_peaks(params[start:end])

            if len(peaks) >0:
                labelled.append(np.max(peaks))
               
                #labelled.append(norm[start-5+peaks[0]])
                # labelled.append([word,func(params[start:end])])
                
            else:
                labelled.append(0.0)
        else:
            #labelled.append([word, func(params[start-10:end])])
            labelled.append(func(params[start:end]))
        
        #raw_input()
	
    return labelled

