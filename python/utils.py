#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
utils.py
Utility functions for spectrum processing
Created on Sat Jul  3 10:12:40 2021

@author: dcohen

TODO:
    Improve despike algorithm
"""
# Imports
import numpy as np
from numpy import diff
from scipy.signal import butter,filtfilt
import matplotlib.pyplot as plt

def despike(yi,th=0.03):
      
    # Dont change the arry yi - return changes array
    y = np.copy(yi) # use y = yi if it is OK to modify input array
    
    # The weight values for the average function - zeros in the center
    # as they should align with the spike
    avg_weights = np.array([1.,1.,1.,1.,1.,1.,1.,1.,0.,0.,0.,0.,1.,1.,1.,1.,1.,1.,1.,1.])
    
    # Marker list has samples that contain spikes
    marker_list = []
    average_array = np.empty(20,dtype='float64')
    
    # Find the samples that have a high ROC
    for index,x in enumerate(y):
        if index == 0:
            xprev = x
        else:
            ydiff = (x - xprev)/xprev
            if ydiff > th:
                marker_list.append(index)
        xprev = x
    
    #print(f'Spikes detected at: {marker_list}')
    
    # Interate through each marker and process
    for x in marker_list:
        window = y[x-10:x+10]
        # TODO: 
        # Sometimes causes error:
        # TypeError: Axis must be specified when shapes of a and weights differ
        """
        I KNOW WHAT'S WRONG HERE, I PREDICTED THIS WOULD HAPPEN AND FORGOT
        IF A VALUE IN marker_list IS LESS THAN HALF THE WINDOW SIZE (IN THE 
        TEST CASE THE FIRST MARKER IS AT x=6), window = y[x-10:x+10] IS
        EQUAL TO ZERO, WHICH CAUSES THE NP.AVERAGE TO FAIL AS window IS
        ZERO ELEMENTS LONG.  EITHER THE SLICE VALUES FOR WINDOW NEED TO 
        BE ADJUSTED IN THIS CASE, OR I FAIL AND RETURN CLEANLY.  I DON'T
        LIKE THAT OPTION.
        
        THIS WILL HAPPEN WHENEVER A PULSE IS DETECTED AT EITHER EXTREME
        OF THE DATA. 
        
        ONE CASE WHERE IT FAILS IS WHEN I RUN:
        plot_tp.py -f ../../data/rtl-sdr/tp_20210715_013919.csv --start 300 --despike
        
        IT FAILS ON THE 1ST MARKER AT POSITION 6
        """
        # DEBUG
        print(f'x: {x}')
        print(f'marker list{marker_list}')
        print(f'window shape {window.shape}')
        print(f'average_weights shape {avg_weights.shape}')
        # DEBUG
        w_average = np.average(window,weights = avg_weights)
        average_array.fill(w_average)
        # Replace eelments in array with averaged value
        # The size of the window to fill is hard-coded,
        # and needs to be improved
        # A poly fit might be better here
        y[x-5:x+5].fill(w_average)
        
        # ***********************************************************
        # This is for testing only - uncomment line below to plot spike segments
        """
        fig = plt.figure(figsize=(10,5))
        ax=fig.add_axes([0,0,1,1],title = str(x))
        ax.plot(window, color='blue')
        # Plot the weighted average against the sample window to see
        # how well the average represents the data around the spike
        ax.plot(average_array, color='red')
        plt.text(0.5,0.5,str(w_average),horizontalalignment='left',
                 verticalalignment='center', transform = ax.transAxes)
        # This is for testing only uncomment line below to plot spike segments
        """
        # ***********************************************************
        
    return y


def despike2(yi,th=0.03,plot=False):
       # Dont change the arry yi - return changes array
    y = np.copy(yi) # use y = yi if it is OK to modify input array
    
    # The weight values for the average function - zeros in the center
    # as they should align with the spike
    avg_weights = np.array([1.,1.,1.,0.,0.,0.,0.,1.,1.,1.])
    
    # Marker list has samples that contain spikes
    marker_list = []
    average_array = np.empty(10,dtype='float64')
    
    # Find the samples that have a high ROC
    for index,x in enumerate(y):
        if index == 0:
            xprev = x
        else:
            ydiff = (x - xprev)/xprev
            if ydiff > th:
                marker_list.append(index)
        xprev = x
    
    #print(f'Spikes detected at: {marker_list}')
    
    # Interate through each marker and process
    for x in marker_list:
        window = y[x-5:x+5]
        w_average = np.average(window,weights = avg_weights)
        average_array.fill(w_average)
     
        noise_array = np.random.uniform((-w_average*.001), (w_average*.001), 10)
        test_array = average_array + noise_array
        # Replace eelments in array with averaged value
        # The size of the window to fill is hard-coded,
        # and needs to be improved
        # A poly fit might be better here
        #y[x-5:x+5].fill(w_average)
        y[x-5:x+5] = test_array
        
        if plot == True:
            fig = plt.figure(figsize=(10,5))
            ax=fig.add_axes([0,0,1,1],title = str(x))
            ax.plot(window, color='blue')
            # Plot the weighted average against the sample window to see
            # how well the average represents the data around the spike
            ax.plot(test_array, color='green')
            plt.text(0.5,0.5,str(w_average),horizontalalignment='left',
                     verticalalignment='center', transform = ax.transAxes)
    return y

# Lowpass filter
def butter_lowpass_filter(data, cutoff, order, sample_rate):
    nyq = 0.5 * sample_rate  # Nyquist Frequency
    normal_cutoff = cutoff / nyq
    # Get the filter coefficients 
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y


def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError ("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError ("Input vector needs to be bigger than window size.")


    if window_len<3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError ("Window is one of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    
    #return y
    return y[int(window_len/2-1):-int(window_len/2)]


# Exponential weighted moving average
# https://stackoverflow.com/questions/42869495/numpy-version-of-exponential-weighted-moving-average-equivalent-to-pandas-ewm
def numpy_ewma_vectorized_v2(data, window):

    alpha = 2 /(window + 1.0)
    alpha_rev = 1-alpha
    n = data.shape[0]

    pows = alpha_rev**(np.arange(n+1))

    scale_arr = 1/pows[:-1]
    offset = data[0]*pows[1:]
    pw0 = alpha*alpha_rev**(n-1)

    mult = data*pw0*scale_arr
    cumsums = mult.cumsum()
    out = offset + cumsums*scale_arr[::-1]
    return out

# Takes  in 
def getlimits(data):
    pass