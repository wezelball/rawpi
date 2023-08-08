"""
tms.py
Two Mice Spectrometer
@author: D. Cohen

TODO:
    despike should be a parameter with a threshold value, not a boolean
"""
# Imports
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Me utils, matie!
import utils

# Create the parser
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
parser.add_argument('--row',action="store",dest="sky_row",type=int,
                    default=0,help='Signal reference row measuring object of interest.')

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
sky_row = parse_results.sky_row

# Check for broken command-line options
if use_correct and sky_row == 0:
    print('Object of interest row must be specified with --row parameter')
    sys.exit()

# These are some good test parameters
# -f ../../data/rtl-sdr/spec_20210701.csv --ref 2 --row 294

# Read entire dataset in a dataframe
df = pd.read_csv(file_name,header=None)

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

# Print some statistics
print(f'Filename:\t\t\t{file_name}')
print('SPECTROMETER DATA')
print(f'Plot date:\t\t\t{df.iloc[sky_row,0]}')
print(f'Reference plot time (UTC):\t{df.iloc[ref_row,1]}')
print(f'Signal plot time (UTC):\t\t{df.iloc[sky_row,1]}')
print(f'Number of FFT bins:\t\t{fft_num_bins}')
print(f'Reference row number:\t\t{ref_row}')
print(f'Signal row number:\t\t{sky_row}')
print(f'Start column offset:\t\t{startcol_offset}')
print(f'End column offset:\t\t{endcol_offset}')
print(f'use_despike:\t\t{use_despike}')
print(f'use_lowpass:\t\t{use_lowpass}')
print(f'use_correction:\t\t{use_correct}')
print('\n')


# Create row series with the number of columns actually being plotted
sky_row_series = df.iloc[sky_row,startcol:endcol]
ref_row_series = df.iloc[ref_row,startcol:endcol]

# Convert series to numpy arrays woth 'float64' as data type
sky_row_array = sky_row_series.to_numpy().astype('float64')
ref_row_array = ref_row_series.to_numpy().astype('float64')

# What is the axis label?
axis_label = 'Raw '

if use_despike:
    ref_row_array = utils.despike(ref_row_array)
    sky_row_array = utils.despike(sky_row_array)
    axis_label = 'Despiked '

if use_lowpass:
    ref_row_array = utils.butter_lowpass_filter(ref_row_array, 2.5, 2, 90)
    sky_row_array = utils.butter_lowpass_filter(sky_row_array, 2.5, 2, 90)
    axis_label += 'lowpass filtered '

if use_correct:
    sky_row_array = np.divide(sky_row_array,ref_row_array)
    axis_label += 'corrected'

# Create the frequency array
# This calculation is complicated by the start/end offsets
freq_step = (df.iloc[ref_row,3] - df.iloc[ref_row,2]) / fft_num_bins
start_freq = df.iloc[ref_row,2] + startcol_offset * freq_step 
end_freq = df.iloc[ref_row,3] - endcol_offset - freq_step
num_steps = fft_num_bins - startcol_offset - endcol_offset - 1
freq_array = np.linspace(start_freq, end_freq, num = num_steps, endpoint=True)

# **************************** PLOT **********************************
# Plot the baseline with the array

fig = plt.figure(figsize=(10,5))
ax=fig.add_axes([0.1,0.1,0.8,0.8],title = f"Reference Signal Processing, {file_name}")
ax.set_xlabel('Frequency')
ax.set_ylabel('Flux')
ax.plot(freq_array,sky_row_array,label=axis_label, color='black')
ax.legend(loc=(0.05,0.8)) # use a location code

# Plot a vertical line at the specified rest frequency
plt.axvline(x=1420405751.768)
plt.show()
