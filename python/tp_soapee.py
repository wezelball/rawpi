#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tp_soapee.py
Total power measurement using simplesoapy and raw I/Q data

Created on Wed Jul  7 14:51:43 2021
@author: dcohen

TODO:
    Use command-line parameters
"""

# Imports
import sys, select, os
import simplesoapy
import numpy as np
import datetime
import csv
import argparse
import threading
import serial
from binascii import unhexlify
import find_port

class TimerClass(threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)
      self.event = threading.Event()
      #self.count = 10

   def run(self):
      while not self.event.is_set():
         dateSTR = datetime.datetime.now().strftime("%H:%M:%S" )
         print(dateSTR)
         self.event.wait(1)

         if calon == True:
            if dateSTR == calon_time:
               print('CAL ON')

         if caloff == True:
            if dateSTR == caloff_time:
               print('CAL OFF')            

   def stop(self):
      self.event.set()


def get_day_now():
   # Get the "now" day in UTC
   return datetime.datetime.utcnow().strftime('%Y-%m-%d')

def get_time_now():
   # Get the "now" time in UTC
   return datetime.datetime.utcnow().strftime('%H:%M:%S')

# Create the parser
parser = argparse.ArgumentParser(description='Record total power to csv file')

# Add the arguments
parser.add_argument('-f', action="store", dest="filename", type=str, default='',\
                    help='Complete path and filename')
parser.add_argument('--tint',action="store",dest="tint",type=int,
                    default=1,help='Integration time in seconds, default 1')
# maybe default gain is too high - airspy won't take this, I think
parser.add_argument('--gain',action="store",dest="gain",type=float,
                    default=49.5,help='SDR gain, default 49.5')
parser.add_argument('--freq',action="store",dest="freq",type=float,
                    default=1420.4e6,help='SDR frequency, default 1420.4e6')
# TODO: check valid gains for RTL-SDR
parser.add_argument('--rate',action="store",dest="sample_rate",type=float,
                    default=2.4e6,help='SDR sample rate, default 2.4e6')
# If using a USB relay to switch a noise source
parser.add_argument('--calon',action="store",dest="calon",type=str,
                    default='',help='Calibration noise source ON time, in UTC (HH:MM:SS)')
parser.add_argument('--caloff',action="store",dest="caloff",type=str,
                    default='',help='Calibration noise source OFF time, in UTC (HH:MM:SS)')

# Parse the arguments

parse_results = parser.parse_args()

file_name = parse_results.filename
t_int = parse_results.tint
gain = parse_results.gain
freq = parse_results.freq
sample_rate = parse_results.sample_rate
calon_time = parse_results.calon
caloff_time = parse_results.caloff

# Some sanity checks on command-line options
if calon_time != '':
   calon = True
else:
   calon = False

if caloff_time != '':
   caloff = True
else:
   caloff = False

# Need cal times checking

# Handle the calibration relay
if calon or caloff:
   # Detect USB devices, get the port of the serial relay if it exists
   usb_devices = find_port.list_devices()
   vendor = usb_devices[0][0]
   usb_port = usb_devices[0][3]

   print(vendor)
   print(usb_port)

   # Open the serial port
   if vendor == '1a86':    # look for the little relay
      relay = serial.Serial()
      relay.port=usb_port
      relay.baudrate=9600
      relay.open()

   # Relay ON/OFF commands
   relay_onstr = "A00101A2"
   relay_offstr = "A00100A1"

tmr = TimerClass()
tmr.start()

# List all connected SoapySDR devices
print(simplesoapy.detect_devices(as_string=True))

# Initialize SDR device
sdr = simplesoapy.SoapyDevice('driver=rtlsdr')

# Set sample rate
#sdr.sample_rate = 2.4e6
sdr.sample_rate = sample_rate

# Set center frequency
#sdr.freq = 1420.4e6
sdr.freq = freq

# Set the gain
#sdr.gain = 49.5
sdr.gain = gain

# Desired integration time, in seconds
#t_int = 10

# N is the number of samples to take, based on integration time and
# sample rate
N = int(sdr.sample_rate * t_int)

# Create the file name and set up CSV writer
if file_name == '':
   file_name = 'tp_' + get_day_now().replace('-', '') + '_' \
       + get_time_now().replace(':', '') + '.csv'

# Loop counter
i = 0

with open(file_name, mode='w') as csv_file:
   csv_writer = csv.writer(csv_file, delimiter=',')

   # Try taking a set of points
   #while True:
   while i < 10:	    
      # Setup base buffer and start receiving samples. Base buffer size is determined
      # by SoapySDR.Device.getStreamMTU(). If getStreamMTU() is not implemented by driver,
      # SoapyDevice.default_buffer_size is used instead
      sdr.start_stream()

      # Create numpy array for received samples
      #samples = numpy.empty(len(sdr.buffer) * 100, numpy.complex64)

      # Setting the buffer size as the number of samples per integration period, N 
      print(f'SDR buffer length: {len(sdr.buffer)}')  
      iq_sample_arr = np.empty(N, np.complex64)

      # Receive all samples
      sdr.read_stream_into_buffer(iq_sample_arr)

      # Stop receiving
      sdr.stop_stream()

      # Now there is a complex array full of samples.  Do some math on it to get
      # a single total power value.

      # It would be nice to know the actual length of the array
      print(f'Sample buffer shape: {iq_sample_arr.shape}')

      # The below is a total power measurement equivalent to summing
      # P = V^2 / R = (sqrt(I^2 + Q^2))^2 = (I^2 + Q^2)
      # Multiplying a complex number by it's conjugate is equal to
      # the square of it's absolute value.
      # (I + jQ) * (I - jQ) = sqrt(I^2 + Q^2)
      p_tot = np.sum(np.real(iq_sample_arr * np.conj(iq_sample_arr)))    

      # Compute the average power value based on the number of samples
      p_avg = p_tot / N

      # Write the power data to current row
      csv_writer.writerow([get_day_now(), get_time_now(), p_avg])
      csv_file.flush()
      print(f'Wrote record {i}\t{get_time_now()}\t{p_avg}')
      i += 1

      # Press enter to terminate program
      print('Press <Enter> to terminate program')
      if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
         break

csv_file.close()
