#!/usr/bin/env python
# Michael Saunby. April 2013   
# 
# Read temperature from the TMP006 sensor in the TI SensorTag 
# It's a BLE (Bluetooth low energy) device so using gatttool to
# read and write values. 
#
# Usage.
# sensortag_test.py BLUETOOTH_ADR
#
# To find the address of your SensorTag run 'sudo hcitool lescan'
# You'll need to press the side button to enable discovery.
#
# Notes.
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#

import pexpect
import sys
import time
import pyupm_i2clcd as lcd


# Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
myLcd = lcd.Jhd1313m1(0, 0x3E, 0x62)
 
myLcd.setCursor(0,0)
# RGB Blue
myLcd.setColor(53, 39, 249)



def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t

cur_temperature = 0


bluetooth_adr = sys.argv[1]
tool = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' -I')
tool.expect('\[LE\]>')
print "Preparing to connect. You might need to press the side button..."
tool.sendline('connect')
# test for success of connect
tool.expect('Connection successful')
tool.sendline('char-write-req 0x2b 0x01')
tool.expect('\[LE\]>')
try:
    while True:
   # time.sleep(1)
  #  tool.sendline('char-read-hnd 0xff07')
        tool.expect('Notification handle = 0x002a value: 34.*')
        rval = tool.after.split()
        num1 = floatfromhex(rval[10])
        num2 = floatfromhex(rval[11])
        #lock
        cur_temperature = (num1 + num2 * 256) / 10
        pr = str(cur_temperature) + " c"
        #unlock
        myLcd.setCursor(0, 0)
        myLcd.write("          ")
        myLcd.write(pr)
        time.sleep(1)
        print cur_temperature
except KeyboardInterrupt:
    exit
    
