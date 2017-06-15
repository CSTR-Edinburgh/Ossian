import math
from scipy import stats
import numpy as np

def get_subsections(trajectory):
    '''
    get subsections as in Murray et al. (2006):
    '''
    new_features = {}
#     frame_rate = 5  ## 5ms per frame
#     c = 100 / frame_rate  ## c frames per 100ms

    t = len(trajectory)

    new_features['whole']      = trajectory
    new_features['half1']      = trajectory[:(t/2)]
    new_features['half2']      = trajectory[(t/2):]
    new_features['quarter1']   = trajectory[:(t/4)]
    new_features['quarter2']   = trajectory[(t/4):(t/2)]
    new_features['quarter3']   = trajectory[(t/2):(t-(t/4))]
    new_features['quarter4']   = trajectory[(t-(t/4)):]
#         new_features['first100ms'] = trajectory[:c]
#         new_features['first200ms'] = trajectory[:(c*2)]
#         new_features['last100ms'] = trajectory[-c:]
#         new_features['last200ms']  = trajectory[-(c*2):]

    return new_features



### feature functions:
def feature_mean(seq):
    return np.mean(seq) #, axis=0)

def feature_std(seq):
    return np.std(seq) #, axis=0)

def feature_min(seq):
    return np.min(seq) # , axis=0)
    
def feature_max(seq):
    return np.max(seq) # , axis=0)
            
def feature_range(seq):
    return feature_max(seq) - feature_min(seq)

def feature_slope(seq):
#    m,n = np.shape(seq)
#    gradients = []
#    for dimension in xrange(n):
#    data = seq[:,dimension]
    gradient, intercept, r_value, p_value, std_err, fit_line = fit_lm(seq)
    return gradient
#    gradients.append(gradient)
#    return np.array(gradients)

def fit_lm(y):   
    x = np.array(range(len(y)))
    gradient, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    fit_line = [(x_val * gradient) + intercept for x_val in x]
    return gradient, intercept, r_value, p_value, std_err, fit_line

def get_stats_over_subsections(data):
    '''
    Compute several statistics over several subsections of the given data, 
    return in a dictionary whose keys indicate the statistic and subsection
    '''
    subsections = get_subsections(data)
    stats = {}
    for (subsection,subdata) in subsections.items():
        for feat_func in [feature_mean, feature_std, feature_range,  feature_min, feature_max, feature_slope]:
            func_name = feat_func.__name__
            func_val = feat_func(subdata)
            stats["%s_%s"%(subsection, func_name)] = func_val
    return stats



