#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 14 07:31:43 2021

tempcal.py
Temperature calibration script

Notes:
    1. Don't use the calibration relay when calibrating temperature


TODO:
    Try smoothing the temperature data, that is noisy due to limited resolution

@author: dcohen
"""
import sys
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
# My utilities
import utils as u

# We're not parsing here yet, so just set some hardcoded values
file_name = 'tp_20210813_temp.csv'
startoff = 1250
endoff = 0
use_smoothing = True
smooth_winsize = 50


# Load the file
try:
    # Read column 1 NOT as dates
    df = pd.read_csv(file_name,header=None)
except FileNotFoundError:
    print('Please specify a valid path filename with --filename.')
    sys.exit()
    
# These are the new changes to get the proper datetime64[ns] values that 
# matplotlib needs.
# Combine the date and time column to a series which is date plus time,
# raw_time_series, and convert to datetime64[ns]
raw_time_series = df[0] + ' ' + df[1]
raw_time_series = pd.to_datetime(raw_time_series)

# Create the total power and time arrays from the pandas dataframe
tp_array = df[2].to_numpy()
time_array = raw_time_series.to_numpy()
temperature_array = df[4].to_numpy()

# smooth filtering was chosen
if use_smoothing:
    tp_array = u.smooth(tp_array, window_len=smooth_winsize)


# I need to get the columns of the dataframe into a series, then convert to
# numpy array, then slice based on start and end offsets
# All of that is done in one line of code!
# These series are "windows" into the main arrays which will be 
# mapped to a plot 
if endoff == 0:
    tp_array_window = tp_array[startoff:]
    time_array_window = time_array[startoff:]
    temperature_array_window = temperature_array[startoff:]
else:
    tp_array_window = tp_array[startoff:-endoff]
    time_array_window = time_array[startoff:-endoff]
    temperature_array_window = temperature_array[startoff:-endoff]
    


# Need to rearrange arrays in ascending temperature
# Sort both arrays
#array_one_sorted = np.sort(array_one)
#array_two_sorted = array_two.ravel()[array_one.argsort(axis=None).reshape(array_one.shape)]
temperature_array_sorted = np.sort(temperature_array_window)
tp_array_sorted = tp_array_window.ravel()[temperature_array_window.argsort(axis=None).reshape(temperature_array_window.shape)]

# calculate polynomial equation
z = np.polyfit(temperature_array_sorted, tp_array_sorted, 3)
f = np.poly1d(z)

# calculate new x's and y's
#temperature_fit = np.linspace(tp_array_sorted[0], tp_array_sorted[-1], 50)
#tp_fit = f(temperature_fit)
tp_fit = f(temperature_array_sorted)

# Plot total power and temperature vs. time
fig1, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(10,5), \
                                  gridspec_kw={'height_ratios': [3,1]})

ax1.set_title(f"Total Power Plot, {file_name}", fontsize = 10)
# This formats the x-axis to hours and minutes only
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
# It actually makes a difference which axis gets plotted first
# Plotting the raw axis then the processed axis makes the graph 
# a lot more readable

ax1.plot(time_array_window, tp_array_window,label='ax1', color='black')
ax1.legend(loc=(0.05,0.8)) # use a location code

ax2.set_title("Ambient Temperaturee, degrees C", fontsize=10)
# This formats the x-axis to hours and minutes only
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
# This will break when any offsets are defined - need to define
# temperature_array_window the same way that other windows are defined
ax2.plot(time_array_window, temperature_array_window)

# Plot total power vs. temperature, with fitted poly
fig2 = plt.figure(figsize=(10,5))
ax3=fig2.add_axes([0,0,1,1],title = f"Reference Signal Processing, {file_name}")
ax3.plot(temperature_array_sorted,tp_array_sorted,label='Tpower', color='black')
ax3.plot(temperature_array_sorted,tp_fit,label='f(temp)', color='red')

# No wasted space
fig1.tight_layout()
fig2.tight_layout()
plt.show()