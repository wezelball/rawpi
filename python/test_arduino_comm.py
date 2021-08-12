#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_ardiono_comm.py

@author: dcohen
"""

# Imports
import serial
import find_port
# For key capture
import termios, fcntl, sys, os

# Determine the serial port the Arduino is on
# Detect USB devices, get the port of the serial relay if it exists
usb_devices = find_port.list_devices()
vendor = usb_devices[0][0]
usb_port = usb_devices[0][3]
            
print(f'USB device vendor: {vendor}')
print(f'USB port: {usb_port}')

# Open the serial port
if vendor == '0403':
    print("Arduino found")
    
"""
duration = 30

   try:
      while i < duration:
         try:
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
      
            # Write the power data to current row
            csv_writer.writerow([get_day_now(), get_time_now(), p_avg, calstate])
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
  """