#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_tp.py
Plots total power files created by tp_soapee.py

Created on Fri Jul  9 07:21:39 2021
@author: dcohen

TODO:
Need a straight line fit for baseline correction    
"""

# Imports
import sys
import pandas as pd
import numpy as np
# my pandas dun tole me, to do da next line, baby yeahhh...
from pandas.plotting import register_matplotlib_converters
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import argparse

# My utilities
import utils as u

# Create the parser
parser = argparse.ArgumentParser(description='Plot total power files created by tp_soapee.py')

# Add the arguments
parser.add_argument('-f', action="store", dest="filename", type=str, default='',\
                    help='Complete path and filename')
parser.add_argument('--start',action="store",dest="startoff",type=int,
                    default=0,help='Offset from starting of data in samples, default 0')
parser.add_argument('--end',action="store",dest="endoff",type=int,
                    default=0,help='Offset from end of date in samples, default 0')
parser.add_argument('--smooth',action="store",dest="smooth",type=int,
                    default=0,help='Use smoothing filter on raw data with specified window size')
# For these arguments, just calling them without an argument sets them 
# to True. Sweet!
# That being said, maybe some of these arguments should be accompanied by a
# parameter, like a threshold value for despike
parser.add_argument('--despike', dest='use_despike', action='store_true', 
                    help='Use despike filer on raw data')
parser.add_argument('--lowpass', dest='use_lowpass', action='store_true', 
                    help='Use lowpass filter on raw data')
parser.add_argument('--overlay', dest='plot_overlay', action='store_true', 
                    help='Graph processed graph over raw data')

"""
TODO - figure this out
parser.add_argument('--correct', dest='use_correct', action='store_true', 
                    help='Use baseline correction for final plot. Requires --ref to be set')
"""

# Parse the arguments
parse_results = parser.parse_args()

file_name = parse_results.filename
startoff = parse_results.startoff
endoff = parse_results.endoff
use_despike = parse_results.use_despike
use_lowpass = parse_results.use_lowpass
plot_overlay = parse_results.plot_overlay
# A windowsize of 200 seems to work well
smooth_winsize = parse_results.smooth
#use_correct = parse_results.use_correct

# useful arguments
# --start 200 --despike --smooth 200

# Check for broken command-line options
if startoff < 0 or endoff < 0:
    print(f'Offsets must be positive integers')
    sys.exit()

if smooth_winsize > 0:
    use_smoothing = True
else:
    use_smoothing = False

# Load the file
try:
    # Read column 1 as dates
    df = pd.read_csv(file_name,header=None, parse_dates=[1])
except FileNotFoundError:
    print('Please specify a valid path filename with --filename.')
    sys.exit()
    
    
# The first column 0, the date, is not currently used in the plot. Pick
# columns 1 and 2 and create a dataframe
tp_df = df[[1,2]]

# I need to get the columns of the dataframe into a series, then convert to
# numpy array, then slice based on start and end offsets
# All of that is done in one line of code!
if endoff == 0:
    tp_array = df[2].to_numpy()[startoff:]
    time_array = df[1].to_numpy()[startoff:]
else:
    tp_array = df[2].to_numpy()[startoff:-endoff]
    time_array = df[1].to_numpy()[startoff:-endoff]

# What is the axis label?
axis_label = 'Raw '

if plot_overlay:
    raw_array = np.copy(tp_array)

if use_despike:
    tp_array = u.despike(tp_array, th=0.005)
    axis_label = 'despiked'
    print('Using despike filter')

# smooth filtering was chosen
if use_smoothing:
    tp_array = u.smooth(tp_array, window_len=smooth_winsize)
    axis_label += ' smoothed'
    print('Using smoothing filter')

# lowpass filtering was chosen
if use_lowpass:
    tp_array = u.butter_lowpass_filter(tp_array,0.5, 2, 90)
    axis_label += ' lowpass filtered'
    print('Using lowpass filter')

"""
# Let's see if a linear regression works for determining a baseline
samples = np.arange(0, tp_array.size, 1)
baseline = np.polyfit(samples,tp_array,1)
baseline_poly = np.poly1d(baseline)
print(baseline_poly)
"""

# Plot total power versus time
# my pandas dun tole me, to do da next line, baby yeahhh...
register_matplotlib_converters()

fig = plt.figure(figsize=(10,5))
ax=fig.add_axes([0,0,1,1],title = f"Total Power Plot, {file_name}")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H-%M"))
# It actually makes a difference which axis gets plotted first
# Plotting the raw axis then the processed axis makes the graph 
# a lot more readable
if plot_overlay:
    ax.plot(time_array,raw_array,color='red' )
ax.plot(time_array, tp_array,label=axis_label, color='black')
ax.legend(loc=(0.05,0.8)) # use a location code

print('PLOT STATISTICS')
print(f'Total number of points: {tp_df.size}')
print(f'Number of points in window: {tp_df.size - startoff - endoff}')
print(f'Array size: {tp_array.size}')
print(f'Start offset: {startoff}')
print(f'End offset: {endoff}')
print(f'Window minimum: {np.amin(tp_array)}')
print(f'Window maximum: {np.amax(tp_array)}')
print(f'Window average: {np.mean(tp_array)}')
print(f'Window stddev: {np.std(tp_array)}')
