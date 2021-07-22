#!/usr/bin/env python
# coding: utf-8

# # Testing a New Despike Algorithm

# In[1]:


# Imports
import sys
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


# In[2]:


# Part of the FWHM
def peak(x, c):
    return np.exp(-np.power(x - c, 2) / 16.0)


# In[3]:


# Part of the FWHM
# Draws the horiz line
def lin_interp(x, y, i, half):
    return x[i] + (x[i+1] - x[i]) * ((half - y[i]) / (y[i+1] - y[i]))


# In[4]:


# This is the hanging nuts of the FWHM
def half_max_x(x, y):
    half = max(y)/2.0 
    #half = max(y)/16.0
    signs = np.sign(np.add(y, -half))
    zero_crossings = (signs[0:-2] != signs[1:-1])
    zero_crossings_i = np.where(zero_crossings)[0]
    return [lin_interp(x, y, zero_crossings_i[0], half),
            lin_interp(x, y, zero_crossings_i[1], half)]


# In[5]:


def despike_f(yi,th=0.03):
    # Dont change the array yi - return changes array
    y = np.copy(yi) # use y = yi if it is OK to modify input array
    # This is the window that contains the spike and some local background on either side
    # Lets's force it to be an odd number so there are equal points on either side of spike
    windowsize = 11
    # Marker list has samples that contain spikes
    marker_list = []
    
    # Find the samples that have a high ROC
    for index,x in enumerate(y):
        if index == 0:
            xprev = x
        else:
            ydiff = (x - xprev)/xprev
            if ydiff > th:
                marker_list.append(index)
        xprev = x
    
    print(f'Spikes detected at: {marker_list}')
    
    # Interate through each marker and process
    for marker in marker_list:
        # This should place the peak in the center of the window
        window_y = y[int(marker-(windowsize-1)/2):int(marker+(windowsize-1)/2+1)]
        print(f'Marker: {marker}\twindow: {window_y}')
        print(f'Peak: {np.amax(window_y)}')
        print('')
        window_x = np.arange(0, window_y.size, dtype='int')
        
        print(f'window_x: {window_x}')
        print(f'window_y: {window_y}')
        
        # find the two crossing points
        hmx = half_max_x(window_x,window_y)
        print(f'hmx: {hmx}')
        
        # Plot each pulse window
        if plot_pulse == True:
            fig = plt.figure(figsize=(10,5))
            ax=fig.add_axes([0,0,1,1],title = str(marker))
            ax.plot(window_y, color='blue')
            # Plot a vertical line at peak of the array
            xmax = np.argmax(window_y==window_y.max())
            plt.axvline(x=xmax)
    
    return y


# In[6]:


# Some global variables
file_name = '../data/rtl-sdr/tp_20210715_013919.csv'
startoff = 300
endoff = 0
use_despike = True
plot_pulse = True


# In[7]:


# Load the file
try:
    # Read column 1 as dates
    df = pd.read_csv(file_name,header=None, parse_dates=[1])
except FileNotFoundError:
    print('Please specify a valid filename')
    sys.exit()


# In[8]:


# The first column 0, the date, is not currently used in the plot. Pick
# columns 1 and 2 and create a dataframe
tp_df = df[[1,2]]


# In[9]:


# I need to get the columns of the dataframe into a series, then convert to
# numpy array, then slice based on start and end offsets
# All of that is done in one line of code!
if endoff == 0:
    tp_array = df[2].to_numpy()[startoff:]
    time_array = df[1].to_numpy()[startoff:]
else:
    tp_array = df[2].to_numpy()[startoff:-endoff]
    time_array = df[1].to_numpy()[startoff:-endoff]


# In[10]:


# Test the despike
if use_despike:
    tp_array = despike_f(tp_array, th=0.015)
    print('Using despike filter')


# In[ ]:


fig = plt.figure(figsize=(10,5))
ax=fig.add_axes([0,0,1,1],title = f"Total Power Plot, {file_name}")
ax.plot(tp_array,label='total power', color='black')
ax.legend(loc=(0.05,0.8)) # use a location code


# In[ ]:




