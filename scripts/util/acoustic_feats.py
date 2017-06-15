import numpy as np
import sys

from speech_manip import spline_smooth_fzero

# gaussian type smoothing, convolution with hamming window
def _smooth(params, win, type="HAMMING"):
    

    win = int(win+0.5)
    if win >= len(params)-1:
        win = len(params)-1
    if win % 2 == 0:
        win+=1

    s = np.r_[params[win-1:0:-1],params,params[-1:-win:-1]]

    
    if type=="HAMMING":
        w = np.hamming(win)
        third = int(win/5)
        #w[:third] = 0
    else:
        w = np.ones(win)
        
        
    y = np.convolve(w/w.sum(),s,mode='valid')
    return y[(win/2):-(win/2)]
    

def _interpolate_zeros(params, method='pchip', min_val = 0):
    import scipy.stats
    import scipy.interpolate
    voiced = np.array(params, float)        
    voiced[voiced<=min_val] = np.nan

    if np.isnan(voiced[-1]):
        voiced[-1] = np.nanmin(voiced)
    if np.isnan(voiced[0]):
        voiced[0] = scipy.stats.nanmean(voiced)

    not_nan = np.logical_not(np.isnan(voiced))
    indices = np.arange(len(voiced))
    if method == 'spline':
        interp = scipy.interpolate.UnivariateSpline(indices[not_nan],voiced[not_nan], k=2) #, s=0.5)
        # return voiced parts intact
        smoothed = interp(indices)
        for i in range(0, len(smoothed)):
            if params[i] > min_val:
                smoothed[i] = params[i]
        return smoothed
    elif method =='pchip':

        interp = scipy.interpolate.pchip(indices[not_nan], voiced[not_nan])
    else:
        interp = scipy.interpolate.interp1d(indices[not_nan], voiced[not_nan], method)
    return interp(indices)




# true envelope style smoothing with varying window
def _peak_smooth(params, max_iter, win,min_win=2,voicing=[]):

    smooth=np.array(params)
    win_reduce =  np.exp(np.linspace(np.log(win),np.log(min_win), max_iter))
   
    TRACE = False
    if TRACE:
        pylab.plot(params, 'black')
    for i in range(0,max_iter):

        smooth = np.maximum(params,smooth)
        if TRACE:
            if i> 0 and i % 10 == 0:
                pylab.plot(smooth,'gray',linewidth=1)
       
        if len(voicing) >0:
            smooth = _smooth(smooth,int(win+0.5)) #,type='rectangle')
            smooth[voicing>0] = params[voicing>0]
        else:
            smooth = _smooth(smooth,int(win+0.5))#,type='rectangle')

        win = win_reduce[i]
    
    if TRACE:
        pylab.plot(smooth,'red',linewidth=2)
        raw_input()

    return smooth


def process(filename, param_type=None, voicing = [], n_coeff = 1):
    
    param_type = param_type.lower()
    try:
        param = np.loadtxt(filename)
    except:
        from scipy.io import wavfile
        fs, param = wavfile.read(sys.argv[1]+".wav")


    
    processed = np.array(param)
   
    

    # for f0, handle boundaries, remove outliers and interpolate zeros
    if param_type =="f0_antti":
        TRACE = True
        fix = True
        if TRACE:
            import pylab
            pylab.plot(param)
        voiced = np.nonzero(param)
        # 1) set start silence to median and end silence to min
        first_v=voiced[0][0]
        last_v = voiced[0][-1]
        processed[:first_v] = np.median(param[voiced])
        processed[last_v:]= np.min(param[voiced])
        processed[param==0] = np.min(processed[voiced])
        
        if fix:
           
            # 2) remove gross outliers
            
            ## 2a) true envelope style smoothing with varying (rectangular) window
            processed = _peak_smooth(processed, 200,10, voicing=param)
            smooth = _smooth(processed, 100)
            param[abs(processed/smooth)>1.3] = 0
            processed[abs(processed/smooth)>1.3] = np.min(processed)
            processed = _peak_smooth(processed, 200,20, voicing=param)

            # constrain speed of change
            diff = np.array(processed)
            diff[1:] = np.diff(processed)
            diff[1:] = _smooth(diff[1:], 5)
            processed = np.cumsum(diff)

            # update unvoiced defualts
            processed[:first_v] = np.median(processed)
            processed[last_v:]= np.min(processed)
            processed[param==0] = np.min(processed)


            
        #fill unvoiced gaps
        processed = _peak_smooth(processed, 200,20, voicing=param)

        #smooth transitions
        processed = _peak_smooth(processed, 10,5)

      
        if TRACE:
            pylab.plot(processed,'black',linewidth=2)

        if TRACE:
            raw_input()
            
    

    # for f0, handle boundaries, remove outliers and interpolate zeros
    if param_type =="f0":
        TRACE = False
        if TRACE:
            import pylab
            pylab.plot(param)    
        processed = spline_smooth_fzero(param, trim_n_frames=4, s=200, k=1)
        if TRACE:
            pylab.plot(processed,'black',linewidth=2)
        if TRACE:
            raw_input()
            pylab.clf()
            
            
    # for gain, remove log, find envelope that fills unvoiced parts
    elif param_type=="gain":
        import scipy.signal
        processed = scipy.signal.medfilt(param, 3)
        processed =  np.e**(processed*0.1)
        
        processed = _peak_smooth(processed,100,8,voicing=voicing)


    return processed


def duration(labels):
    """
    make a continuous duration signal from time labels
    x-axis = time
    y-axis = log-duration
    """
    
    TRACE = False
    if TRACE:
        import pylab
        pylab.figure()
  
    params = np.zeros(labels[-1][1])
    
    for i in range(len(labels)):
        (st,en,phn) = labels[i]
        params[int(st+(en-st)/2.0)] = np.log(en-st)

    
    # fix gaps
  
    for i in range(len(labels)-1):
        cur = labels[i][1]
        next = labels[i+1][0]
        if cur != next:
            params[int(cur+(next-cur)/2.0)] = 1 #np.log(next-cur)
    
    if labels[0][0] != 0:
        params[labels[0][0]/2.0] = 1 #np.log(labels[0][0]/2.0)
  
        
    params = _interpolate_zeros(params,'pchip') #,'linear')
    

    if TRACE:
        pylab.plot(params, label="interpolated",linewidth=2)
        #cwt_utils.plot_labels(labels,ypos=-2)
        pylab.plot(params)
        raw_input()

    # for boundaries, look at derivative, i.e. change from slow ta fast
    #params[:-1] = np.diff(params,1)
    #params[-1] = params[-2]

    if TRACE:
        pylab.plot(params*30, label="difference",linewidth=2)
        pylab.legend()
        raw_input()
  
    return params


