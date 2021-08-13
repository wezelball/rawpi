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
import sys, time

# VID for the Arduino Nano
vendor_id = '0403'

# Determine the serial port the Arduino is on
# use this code to replace old USB port code
try:
    usb_device = find_port.list_devices(vid=vendor_id)           
    usb_port = usb_device[0][3]
    print(f'USB port: {usb_port}')
    nano = serial.Serial()
    nano.port=usb_port
    nano.baudrate=57600
    nano.open()
except:
    sys.exit('No Arduino found')


# setup loop
duration = 10
i = 0

# loop
while i < duration:
    print(f'Loop: {i}')
    i += 1
    nano.write(b't')    # the b encodes to byte, not unicode (Python default string)
    time.sleep(1)
    if nano.inWaiting()>0:
        # This needs to come after time.sleep() or the zeroth temperature
        # wont be set
        temperature = float(nano.read(nano.inWaiting()))
        print(temperature)

