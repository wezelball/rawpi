#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aniview.py

Generates an animated preview of a CSV data file
Created on Sat Jul  3 09:13:45 2021

@author: dcohen

TODO:

"""

# Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import imageio
import os, sys
# My own utility functions
import utils
# For displaying the animation
from tkinter import * 
from PIL import Image, ImageTk

# Thanks, stackoverflow
# https://stackoverflow.com/questions/7960600/python-tkinter-display-animated-gif-using-pil
class MyLabel(Label):
    def __init__(self, master, filename):
        im = Image.open(filename)
        seq =  []
        try:
            while 1:
                seq.append(im.copy())
                im.seek(len(seq)) # skip to next frame
        except EOFError:
            pass # we're done

        try:
            self.delay = im.info['duration']
        except KeyError:
            self.delay = 100

        first = seq[0].convert('RGBA')
        self.frames = [ImageTk.PhotoImage(first)]

        Label.__init__(self, master, image=self.frames[0])

        temp = seq[0]
        for image in seq[1:]:
            temp.paste(image)
            frame = temp.convert('RGBA')
            self.frames.append(ImageTk.PhotoImage(frame))

        self.idx = 0

        self.cancel = self.after(self.delay, self.play)

    def play(self):
        self.config(image=self.frames[self.idx])
        self.idx += 1
        if self.idx == len(self.frames):
            self.idx = 0
        self.cancel = self.after(self.delay, self.play)


def stop_it():
    anim.after_cancel(anim.cancel)


# Create the parser
parser = argparse.ArgumentParser(description='Create an animated GIF from CSV file created by soapy_power')
# Add the arguments
parser.add_argument('--startrow', action="store", dest="start_row", type=int,
                    default=0,help='Select starting row for animation, default 0')
parser.add_argument('--endrow', action="store", dest="end_row", type=int,
                    default=0,help='Select ending row for animation, default last')
parser.add_argument('-f', action="store", dest="filename", type=str, default='',\
                    help='Complete path and filename')
parser.add_argument('--startoff',action="store",dest="startcol_off",type=int,
                    default=0,help='Offset from starting column of plot in samples, default 0')
parser.add_argument('--endoff',action="store",dest="endcol_off",type=int,
                    default=0,help='Offset from ending column of plot in samples, default 0')
parser.add_argument('--fps',action="store",dest="fps",type=int,
                    default=1,help='Frame rate in fps, default 1')
parser.add_argument('--ref',action="store",dest="ref",type=int,
                    default=0,help='Cold sky reference row. Required when using --correct')
parser.add_argument('--chartmin',action="store",dest="chartmin",type=float,
                    default=-999.0,help='Min value of Y axis in chart.  Default is auto min. Must set --chartmax as well')
parser.add_argument('--chartmax',action="store",dest="chartmax",type=float,
                    default=-999.0,help='Max value of Y axis in chart.  Default is auto max. Must set --chartmin as well')
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
start_row = parse_results.start_row
end_row = parse_results.end_row
file_name = parse_results.filename
startcol_offset = parse_results.startcol_off
endcol_offset = parse_results.endcol_off
use_despike = parse_results.use_despike
use_lowpass = parse_results.use_lowpass
use_correct = parse_results.use_correct
frame_rate = parse_results.fps
ref_row = parse_results.ref
chartmin = parse_results.chartmin
chartmax = parse_results.chartmax

manual_chart = False

# Load the file
try:
    df = pd.read_csv(file_name,header=None)
except FileNotFoundError:
    print('Please specify a valid path filename with --filename.')
    sys.exit()

# Check for command-line hyjinks
if start_row > end_row and end_row > 0:
    print('Start row cannot be > end row')
    sys.exit()
    
if end_row > len(df):
    print(f'End row cannot be > {len(df)}')
    sys.exit()

if end_row == 0:
    end_row = len(df) - 1

if frame_rate < 0:
    frame_rate = 1
elif frame_rate > 30:
    frame_rate = 30

if start_row < 0 or end_row < 0:
    print(f'Rows must be positive integers')
    sys.exit()

if use_lowpass:
    if not use_despike:
        print("Lowpass filtering requires --despike option")
        sys.exit()

if use_correct and ref_row == 0:
    print("Reference row should be carefully chosen. Using default of 0")

if chartmin > -990.0 or chartmax > -990.0:
    manual_chart = True
    if chartmin < -990.0 or chartmax < -990.0:
         print('Must specify both min and max chart limits, not just one')
         sys.exit()
     

# DEBUG - print results
print(f'start_row: {start_row}')
print(f'end_row: {end_row}')
print(f'file_name: {file_name}')
print(f'startcol_offset: {startcol_offset}')
print(f'endcol_offset: {endcol_offset}')
print(f'use_despike: {use_despike}')
print(f'use_lowpass: {use_lowpass}')
print(f'use_correction: {use_correct}')
if use_correct:
    print(f'reference row: {ref_row}')
print(f'fps: {frame_rate}')

# This selects columns 6 thru last column -1 , which is all the FFT
# data. Not sure whay last column is invalid
# Now an offset is included
startcol = 6 + startcol_offset
endcol = -1 - endcol_offset

# Create animation of file
# Should these be command-line options too?
gif_path = "/home/dcohen/tmp/test.gif"
frames_path = "/home/dcohen/tmp/{i}.jpg"

# Load the reference frame that was specied from command-line
# Convert to float64 or a lot of shit will break
# This is being done prior to looping thru entire file
if use_correct:
    ref_row_series = df.iloc[ref_row,startcol:endcol]
    ref_row_array = ref_row_series.to_numpy().astype('float64')
    if use_despike:
        ref_row_array = utils.despike(ref_row_array)
    if use_lowpass:
        ref_row_array = utils.butter_lowpass_filter(ref_row_array,2.5, 2, 90)

# Set up the min/max values for the entire processed dataset for 
# the purpose of creating a useful graph scale
dataset_min = 0.0
dataset_max = 0.0

plt.figure(figsize=(8,8))
for i,x in enumerate(range(start_row,end_row+1)):
    # Get observatio data and time for plot
    obsdate = df.iloc[x,0]
    obstime = df.iloc[x,1]
    # Load the row into a numpy array
    row_series = df.iloc[i,startcol:endcol]
    row_series_array = row_series.to_numpy().astype('float64')
    # Despike was chosen
    if use_despike:
        row_series_array = utils.despike(row_series_array)
    # lowpass filtering was chosen
    if use_lowpass:
        row_series_array = utils.butter_lowpass_filter(row_series_array, 2.5, 2, 90)
    # Baseline correction was chosen
    if use_correct:
        # Divide the signal by the reference, which is already preprocessed
        row_series_array = np.divide(row_series_array,ref_row_array)

    # Determine the min and max value of the daate set
    current_max = np.max(row_series_array)
    current_min = np.min(row_series_array)
    
    # Set these equal for the first iteration
    if i == 0:
        dataset_min = current_min
        dataset_max = current_max
    
    # is current maximum > dataset maximum?
    if current_max > dataset_max:
        dataset_max = current_max
        
    # is current maximum > dataset maximum?
    if current_min < dataset_min:
        dataset_min = current_min
        
    # TODO - ylim should be result of calculation based on min and max value of
    # all records - I can add a function to do that 
    if manual_chart == True:
        plt.ylim(chartmin, chartmax)
    plt.plot(row_series_array)
    plt.xlabel(f'Date:{obsdate}, Record:{str(x)}, Time:{obstime}', fontsize = 15)
    plt.savefig("/home/dcohen/tmp/{i}.jpg".format(i=i))
    # The following two lines are a neat little trick to print multiple
    # times in the same place
    print(f'\rCreated image: %d.jpg' %i, end="")
    sys.stdout.flush()
    # Clear the previous plot. Don't do this and all plots will end
    # up on the same figure!
    plt.clf()
# Create the animated GIF file
with imageio.get_writer(gif_path, mode='I', fps = frame_rate) as writer:
    for i in range(end_row-start_row+1):
        writer.append_data(imageio.imread(frames_path.format(i=i)))

# Report the minimum and maximum of the entire dataset
print('\n')
print(f'Dataset minimum: {dataset_min}')
print(f'Dataset maximum: {dataset_max}')

# Animated GIF Player for Tkinter
# Thanks, stackoverflow
# https://stackoverflow.com/questions/7960600/python-tkinter-display-animated-gif-using-pil
root = Tk()
anim = MyLabel(root, gif_path)
anim.pack()
# TODO: button should kill the process
Button(root, text='stop', command=stop_it).pack()
root.mainloop()