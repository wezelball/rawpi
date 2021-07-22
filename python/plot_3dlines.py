#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_3dlines.py
Plots spectral data from soapy_power in 3d format

Created on Fri Jul  9 17:33:37 2021

@author: dcohen

TODO:
    This shares a HUGE amount of code with tmp.py. Is there a pythonic way
    to handle that?
    
    It's plotting 3D data okay, but the observation time is funky
"""

# Imports
import sys
from datetime import datetime
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as dates
from mpl_toolkits.mplot3d.axes3d import Axes3D
import argparse

# My utilities
import utils as u

# Create the parser - this should be common to plot_3dlines.py and tms.py
# What's the best way to do that?
parser = argparse.ArgumentParser(description='Create an animated GIF from CSV file created by soapy_power')
# Add the arguments
parser.add_argument('-f', action="store", dest="filename", type=str, default='',\
                    help='Complete path and filename')
parser.add_argument('--start',action="store",dest="startcol_off",type=int,
                    default=0,help='Offset from starting column of plot in samples, default 0')
parser.add_argument('--end',action="store",dest="endcol_off",type=int,
                    default=0,help='Offset from ending column of plot in samples, default 0')
parser.add_argument('--ref',action="store",dest="ref_row",type=int,
                    default=0,help='Cold sky reference row. Required when using --correct')
parser.add_argument('--startrow',action="store",dest="startrow",type=int,
                    default=0,help='Starting row of plot.')
parser.add_argument('--endrow',action="store",dest="endrow",type=int,
                    default=0,help='Ending row of plot.')

# For these arguments, just calling them without an argument sets them 
# to True. Sweet!
parser.add_argument('--despike', dest='use_despike', action='store_true', 
                    help='Use despike filer on raw data')
parser.add_argument('--lowpass', dest='use_lowpass', action='store_true', 
                    help='Use lowpass filter on raw data')
parser.add_argument('--correct', dest='use_correct', action='store_true', 
                    help='Use baseline correction for final plot. Requires --ref to be set')

# Parse the arguments
parse_results = parser.parse_args()

file_name = parse_results.filename
startcol_offset = parse_results.startcol_off
endcol_offset = parse_results.endcol_off
use_despike = parse_results.use_despike
use_lowpass = parse_results.use_lowpass
use_correct = parse_results.use_correct
ref_row = parse_results.ref_row
start_row = parse_results.startrow
end_row = parse_results.endrow

# Check for broken command-line options
if start_row == 0  and end_row == 0:
    print('Start and end rows the same, nothing to do')
    sys.exit()

# These are some good test parameters
# -f ../../data/rtl-sdr/spec_20210701.csv --ref 2

# Read entire dataset in a dataframe
df = pd.read_csv(file_name,header=None, parse_dates=[1])

# Calculate the FFT number of bins, which is 6 less than the number of columns in the file
# for soapy_power
fft_num_bins = df.shape[1] - 6

# This selects columns 6 thru last column -1 , which is all the FFT
# data. Not sure whay last column is invalid
# Now an offset is included
startcol = 6 + startcol_offset
endcol = -1 - endcol_offset

# The number of columns actually number of bins minus the start and end offsets
num_columns = fft_num_bins - startcol_offset - endcol_offset

# Create the frequency array
# This calculation is complicated by the start/end offsets
freq_step = (df.iloc[ref_row,3] - df.iloc[ref_row,2]) / fft_num_bins
start_freq = df.iloc[ref_row,2] + startcol_offset * freq_step 
end_freq = df.iloc[ref_row,3] - endcol_offset - freq_step
num_steps = fft_num_bins - startcol_offset - endcol_offset - 1
freq_array = np.linspace(start_freq, end_freq, num = num_steps, endpoint=True)


# Print some statistics
print(f'Filename:\t\t\t{file_name}')
print('SPECTROMETER DATA')
print(f'Plot date:\t\t\t{df.iloc[ref_row,0]}')
print(f'Reference plot time (UTC):\t{df.iloc[ref_row,1]}')
print(f'Signal start row plot time (UTC):\t\t{df.iloc[start_row,1]}')
print(f'Signal end row plot time (UTC):\t\t{df.iloc[end_row,1]}')
print(f'Number of FFT bins:\t\t{fft_num_bins}')
print(f'Reference row number:\t\t{ref_row}')
print(f'Starting row number:\t\t{start_row}')
print(f'Ending row number:\t\t{end_row}')
print(f'Start column offset:\t\t{startcol_offset}')
print(f'End column offset:\t\t{endcol_offset}')
print(f'use_despike:\t\t{use_despike}')
print(f'use_lowpass:\t\t{use_lowpass}')
print(f'use_correction:\t\t{use_correct}')
print('\n')

# Create the frequency array
# This calculation is complicated by the start/end offsets
freq_step = (df.iloc[ref_row,3] - df.iloc[ref_row,2]) / fft_num_bins
start_freq = df.iloc[ref_row,2] + startcol_offset * freq_step 
end_freq = df.iloc[ref_row,3] - endcol_offset - freq_step
num_steps = fft_num_bins - startcol_offset - endcol_offset - 1
freq_array = np.linspace(start_freq, end_freq, num = num_steps, endpoint=True)
# Convert frequency array to series

# Using lists for plotting, but change to 

# Instantiate the figure and the axes, and plot BIG
fig, ax = plt.subplots(subplot_kw={'projection': '3d'},figsize=(18,10))
fig.suptitle('3D Plot of Rows')

# Load the reference frame that was specied from command-line
# Convert to float64 or a lot of shit will break
# This is being done prior to looping thru entire file
if use_correct:
    ref_row_series = df.iloc[ref_row,startcol:endcol]
    ref_row_array = ref_row_series.to_numpy().astype('float64')
    if use_despike:
        ref_row_array = u.despike(ref_row_array)
    if use_lowpass:
        ref_row_array = u.butter_lowpass_filter(ref_row_array,2.5, 2, 90)

# Iterate from start row to end row, plotting one line at a time
for row in range(start_row, end_row):
    # Create row series with the number of columns actually being plotted
    row_series = df.iloc[row,startcol:endcol]

    # Get the time for that row
    obstime_str = df.iloc[row,1].lstrip() # there is a leading space the string
    
    # Convert string time into datetime object, then to matplotlib time - jeezus!
    utc_date_time = np.datetime64(datetime.strptime(obstime_str, '%H:%M:%S'))
    
    # I have to do this to get time to plot at all, but it results
    # in funky decimal numbers
    utc_time = dates.date2num(utc_date_time)
    #utc_time = utc_date_time
    
    # Creare power array 
    power_array = row_series.to_numpy().astype('float64')

    # Despike was chosen
    if use_despike:
        power_array = u.despike(power_array)
    # lowpass filtering was chosen
    if use_lowpass:
        power_array = u.butter_lowpass_filter(power_array, 2.5, 2, 90)
    # Baseline correction was chosen
    if use_correct:
        # Divide the signal by the reference, which is already preprocessed
        power_array = np.divide(power_array,ref_row_array)

    # Create the time array, where array is filled with same time
    time_array = np.full(num_columns-1, utc_time).astype('datetime64')

    # Convert to pandas series
    #power_series = pd.Series(power_array)
    #freq_series = pd.Series(freq_array)
    #time_series = pd.Series([utc_time] * (num_columns - 1)).astype('datetime64[ns]')
    #print(type(time_series))

    # Convert to lists
    power_list = power_array.tolist()
    freq_list = freq_array.tolist()
    time_list = [utc_time] * (num_columns - 1)

    # Order the dataset, and plot it
    dataset = {"x":time_list, "y":freq_list, "z":power_list}
    #dataset = {"x":time_series, "y":freq_series, "z":power_series}
    ax.plot(dataset["x"], dataset["y"], dataset["z"], color='blue')
    
    # This is the camera orientation. The 1st parm is the elevation angle, the 2nd parm
    # is the rotation angle
    ax.view_init(45, 0)
    
# Labels
plt.xlabel("Observation time")
plt.ylabel("Frequency")    
