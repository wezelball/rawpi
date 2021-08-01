#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_tp.py
Plots total power files created by tp_soapee.py

Created on Fri Jul  9 07:21:39 2021
@author: dcohen

TODO:

Known Bugs:

Serious - By defining a windows tp_array_window and time_array_window,
I fixed some problems with calibration markers, but I created a new problem-
any operation on the array (smoothing, lowpass, etc) doesn't appear to
affect window.  Maybe if I defined the windows after any post-processing,
but before any plotting.

Serious - if the time wraps around from 23 hours to 00 UTC, the plot
gets flipped on x-axis, and some other weird stuff happens.

THIS BUG HAS BEEN FIXED IN THEORY, BUT ADDT'L TESTING IS NEEDED

Smoothing a plot can cause exception because the size of the smooth versus
raw arrays differs by one element.  This was noticed when trying to plot an
overlay or smooth versus raw data.

When running from spyder, x and y axis values show.  When running from the
command-line, they don't show.  I think this has to to with the Matplotlib
backend module, which differs between spyder and the command line

FIXED - DEFINED ax AS A SUBPLOT 

Plot markers where calibrator changes state - this is working, but needs
more testing.
    
Need a straight line fit for baseline correction    
"""

# Imports
import sys
import pandas as pd
import numpy as np
# my pandas dun tole me, to do da next line, baby yeahhh...
#from pandas.plotting import register_matplotlib_converters
#import matplotlib
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


# Check for broken command-line options
if startoff < 0 or endoff < 0:
    print('Offsets must be positive integers')
    sys.exit()

if smooth_winsize > 0:
    use_smoothing = True
else:
    use_smoothing = False

# Load the file
try:
    # Read column 1 NOT as dates
    #df = pd.read_csv(file_name,header=None, parse_dates=[1])
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


# TODO: THIS BLOCK OF CODE NEEDS TO MOVED AND tp_array_window REDEFINED
# IN TERMS OF # tp_array INSTEAD OF df[2], AS THIS ARRAY HAS BEEN
# MODIFIED BY WHATEVER POST-PROCESSING WAS DONE

# I need to get the columns of the dataframe into a series, then convert to
# numpy array, then slice based on start and end offsets
# All of that is done in one line of code!
# These series are "windows" into the main arrays which will be 
# mapped to a plot 
if endoff == 0:
    tp_array_window = df[2].to_numpy()[startoff:]
    time_array_window = time_array[startoff:]
    
else:
    tp_array_window = df[2].to_numpy()[startoff:-endoff]
    time_array_window = time_array[startoff:-endoff]

# TODO: END OF BLOCK OF CODE

# Set up calibration variables
cal_on_transition = -1
cal_off_transition = -1
calibrating = False

# Was a calibration done?
try:
    cal_series = df[3].str.find('ON')
    # just a test
    for i,j in enumerate(cal_series):
        if cal_on_transition < 0 and j == 0:
            # Have to shift by the starting offset
            cal_on_transition = i
            cal_on_position = i - startoff
            calibrating = True
            print(f'Found cal on at sample: {cal_on_transition}')
        if cal_off_transition < 0 and calibrating and j == -1:
            # Have to shift by the starting offset
            cal_off_transition = i
            cal_off_position = i - startoff
            print(f'Found cal off at sample: {cal_off_transition}')
               
# Older files wont have the calibration field
except KeyError:
    pass

# Need to get time values associated with calibration samples
if calibrating:
    cal_time_on = time_array[cal_on_transition]
    cal_time_off = time_array[cal_off_transition]
    
    print(f'cal time on: {cal_time_on}')
    print(f'cal time off: {cal_time_off}')

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








fig = plt.figure(figsize=(10,5))
# By setting ax as a subplot, the x and y values are now displayed
# when running from the shell
#ax=fig.add_axes([0,0,1,1],title = f"Total Power Plot, {file_name}")
ax = fig.add_subplot(1, 1, 1)
ax.set_title(f"Total Power Plot, {file_name}")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H-%M"))
# It actually makes a difference which axis gets plotted first
# Plotting the raw axis then the processed axis makes the graph 
# a lot more readable
if plot_overlay:
    ax.plot(time_array_window,raw_array,color='red' )
ax.plot(time_array_window, tp_array_window,label=axis_label, color='black')
ax.legend(loc=(0.05,0.8)) # use a location code


# Plot the calibration on/off lines
if calibrating and cal_on_transition != -1 and cal_on_position >= 0:
    plt.axvline(x=cal_time_on)
# TODO: validate the math below, looks like it works
if calibrating and cal_off_transition != -1  and cal_off_position <= (len(df) - startoff - endoff):
    plt.axvline(x=cal_time_off, color = 'red')

plt.show()

print('PLOT STATISTICS')
print(f'Total number of points: {len(df)}')
print(f'Number of points in window: {len(df) - startoff - endoff}')
print(f'Array size: {tp_array.size}')
print(f'Start offset: {startoff}')
print(f'End offset: {endoff}')
print(f'Window minimum: {np.amin(tp_array_window)}')
print(f'Window maximum: {np.amax(tp_array_window)}')
print(f'Window average: {np.mean(tp_array_window)}')
print(f'Window stddev: {np.std(tp_array_window)}')
