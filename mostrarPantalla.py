#!/usr/bin/env python
import time,sys
import requests
import spidev # To communicate with SPI devices
from time import sleep	
from sys import argv, exit
import math

if sys.platform == 'uwp':
    import winrt_smbus as smbus
    bus = smbus.SMBus(1)
else:
    import smbus
    import RPi.GPIO as GPIO
    rev = GPIO.RPI_REVISION
    if rev == 2 or rev == 3:
        bus = smbus.SMBus(1)
    else:
        bus = smbus.SMBus(0)

# this device has two I2C addresses
DISPLAY_RGB_ADDR = 0x62
DISPLAY_TEXT_ADDR = 0x3e

# set backlight to (R,G,B) (values from 0..255 for each)
def setRGB(r,g,b):
    bus.write_byte_data(DISPLAY_RGB_ADDR,0,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,1,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,0x08,0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR,4,r)
    bus.write_byte_data(DISPLAY_RGB_ADDR,3,g)
    bus.write_byte_data(DISPLAY_RGB_ADDR,2,b)

# send command to display (no need for external use)    
def textCommand(cmd):
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)

# set display text \n for second line(or auto wrap)     
def setText(text):
    textCommand(0x01) # clear display
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))

#Update the display without erasing the display
def setText_norefresh(text):
    textCommand(0x02) # return home
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    while len(text) < 32: #clears the rest of the screen
        text += ' '
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))

# Start SPI connection
spi = spidev.SpiDev()
spi.open(0,0)	

# Read MCP3008 data
def analogInput(channel):
    if ((channel > 7) or (channel < 0)):
        return -1
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

#base de datos
url = 'https://corlysis.com:8086/write'
params = {"db": "Datos sensores", "u": "token", "p":"c23fe811d11d8d522dd10863af5bf772"}


def temp(channel):
    bValue = 3975 # sensor v1.0 uses thermistor TTC3A103*39H
    a = analogInput(channel) # call the function to read analog inputs
    resistance = (float)(1023 - a) * 10000 / a
    t = (float)(1 / ((math.log(resistance / 10000) if resistance > 1 else 0 )/ bValue + 1 / 298.15) - 273.15)
    return t


def main():
    try:
        while True:
            #output = analogInput(0) # Reading from CH0
            #setText(str(output))
            #sleep(0.2)
            output = str (analogInput(0)) # Reading from CH0
            output2 = str(analogInput(1)) # Reading from CH1
            output3 = str(temp(2))# Reading from CH2
            output4 = str(analogInput(3)) # Reading from CH2
            setText("H: %s " "L: %s " "  T: %s " "P: %s "%(output, output2, output3[0:5], output4))
            inputHumedad = "humedad,place=universidad value=%d\n" % (analogInput(0))
            inputLuminosidad = "luminosidad,place=universidad value=%d\n" % (analogInput(1))
            inputTemperatura = "temperatura,place=universidad value=%d\n" % (temp(2))
            inputPresion = "presion,place=universidad value=%d\n" % (analogInput(3))
            requests.post(url, params=params, data=inputHumedad)
            requests.post(url, params=params, data=inputLuminosidad)
            requests.post(url, params=params, data=inputTemperatura)
            requests.post(url, params=params, data=inputPresion)
            sleep(0.4) #el sleep lo ponemos a 5 para la BD
    except IndexError:
        print("please, introduce the ADC chanel in which you want to read from.")
        exit(0)

if __name__== "__main__":
    main()

      #output = analogInput(0)
      #print(output)
      #time.sleep(2)
    