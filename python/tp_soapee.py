#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tp_soapee.py
Total power measurement using simplesoapy and raw I/Q data

Created on Wed Jul  7 14:51:43 2021
@author: dcohen

TODO:
    Fix key capture - DONE
    Add calibration markers - IN PROGRESS
"""

# Imports
import simplesoapy
import numpy as np
import datetime
import csv
import argparse
import threading
import serial
from binascii import unhexlify
import find_port
# For key capture
import termios, fcntl, sys, os


class TimerClass(threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)
      self.event = threading.Event()

   def run(self):
      global calstate
      while not self.event.is_set():
         dateSTR = get_time_now()
         self.event.wait(1)

         if calon == True:
            if dateSTR == calon_time:
               print('CAL ON')
               relay.write(unhexlify(relay_onstr))
               calstate = 'ON'

         if caloff == True:
            if dateSTR == caloff_time:
               print('CAL OFF')
               relay.write(unhexlify(relay_offstr))
               calstate = 'OFF'
               
   def stop(self):
      self.event.set()


def get_day_now():
   # Get the "now" day in UTC
   return datetime.datetime.utcnow().strftime('%Y-%m-%d')

def get_time_now():
   # Get the "now" time in UTC
   return datetime.datetime.utcnow().strftime('%H:%M:%S')

# ************************* KEY CAPTURE *************************************
fd = sys.stdin.fileno()

# This will fail if running in Spyder, must run from shell
oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)

oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
# ************************* KEY CAPTURE *************************************

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
parser.add_argument('--duration',action="store",dest="duration",type=int,
                    default=43200,help='Duration of observation in seconds, default 43200 (12 hours)')
# For these arguments, just calling them without an argument sets them 
# to True. Sweet!
parser.add_argument('--temp', dest='record_temperature', action='store_true', 
                    help='Record ambient temperature')

# Parse the arguments

parse_results = parser.parse_args()

file_name = parse_results.filename
t_int = parse_results.tint
gain = parse_results.gain
freq = parse_results.freq
sample_rate = parse_results.sample_rate
calon_time = parse_results.calon
caloff_time = parse_results.caloff
duration = parse_results.duration
recording_temperature = parse_results.record_temperature

# Make up some test parms
#calon = True
#caloff = True
#calon_time = '02:15:00'
#caloff_time = '02:30:00'
#duration = 1800

# Set up calibration logic
if calon_time != '':
   calon = True
else:
   calon = False

if caloff_time != '':
   caloff = True
else:
   caloff = False

calstate = 'OFF'

# Need cal times sanity checking

# Handle the USB devices
if calon or caloff or recording_temperature:
   # Detect USB devices, get the port of the serial relay if it exists
   usb_devices = find_port.list_devices()
   
   if calon or caloff:
       vendor_id = '1a86'
       try:
           usb_device = find_port.list_devices(vid=vendor_id)           
           usb_port = usb_device[0][3]
           relay = serial.Serial()
           relay.port=usb_port
           relay.baudrate=9600
           relay.open()
           print('Calibrator relay found')
       except:
            sys.exit('No calibrator relay found')
            
   if recording_temperature:
        vendor_id = '0403'
        try:
           usb_device = find_port.list_devices(vid=vendor_id)           
           usb_port = usb_device[0][3]
           nano = serial.Serial()
           nano.port=usb_port
           nano.baudrate=57600 # slow this down
           nano.open()
           print('Arduino found')
        except:
            sys.exit('No Arduino found')
   
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
   try:
      while i < duration:
         try:
            # Write to the Arduino, requesting a temperature 
            nano.write(b't')    # the b encodes to byte, not unicode (Python default string)
			
            # Setup base buffer and start receiving samples. Base buffer size is determined
            # by SoapySDR.Device.getStreamMTU(). If getStreamMTU() is not implemented by driver,
            # SoapyDevice.default_buffer_size is used instead
            sdr.start_stream()
      
            # Setting the buffer size as the number of samples per integration period, N 
            #print(f'SDR buffer length: {len(sdr.buffer)}')  
            iq_sample_arr = np.empty(N, np.complex64)
      
            # Receive all samples
            sdr.read_stream_into_buffer(iq_sample_arr)
      
            # Stop receiving
            sdr.stop_stream()
      
            # Now there is a complex array full of samples.  Do some math on it to get
            # a single total power value.
      
            # The below is a total power measurement equivalent to summing
            # P = V^2 / R = (sqrt(I^2 + Q^2))^2 = (I^2 + Q^2)
            # Multiplying a complex number by it's conjugate is equal to
            # the square of it's absolute value.
            # (I + jQ) * (I - jQ) = sqrt(I^2 + Q^2)
            p_tot = np.sum(np.real(iq_sample_arr * np.conj(iq_sample_arr)))    
      
            # Compute the average power value based on the number of samples
            p_avg = p_tot / N

	    # Try to get temperature from Arduino, should be enough time
            temperature = -99.0		# if no temperature data, record something
            if nano.inWaiting()>0:
               temperature = float(nano.read(nano.inWaiting()))
      
            # Write the power data to current row
            csv_writer.writerow([get_day_now(), get_time_now(), p_avg, calstate, temperature])
            csv_file.flush()
            print(f'Wrote record {i}\t{get_time_now()}\t{p_avg}')
            i += 1
            
            # See if a key has been pressed
            c = sys.stdin.read(1)
            if c:
               print("Got character", repr(c))
               # Checking for the escape key, but also for 
               # certain other keys (like the arrows)
               # could do 'q' or 'Q' to quit
               if c == 'q' or c == 'Q':
                  break
         except IOError: pass
          
   finally:
      termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
      fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
  
      csv_file.close()
      tmr.stop()
      if calon or caloff:
         relay.close()
      if recording_temperature:
         nano.close()
