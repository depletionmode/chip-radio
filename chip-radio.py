# Next Thing Co. C.H.I.P-based internet radio build
# @depletionmode, 2016
# 
# Dependancies:
#  * radiopy (https://sourceforge.net/p/radiopy/code/ci/master/tree/radiopy/)
#  * Adafruit_MCP3008 (https://github.com/adafruit/Adafruit_Python_MCP3008)
#  * https://github.com/atenart/dtc
#  * https://github.com/xtacocorex/CHIP_IO
#  * https://github.com/xtacocorex/Adafruit_Python_GPIO

import os
import time
import subprocess

import radiopy.stations_tunein as stations_tunein

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008 as ADC

adc = ADC.MCP3008(spi=SPI.SpiDev(0, 0))

def _get(ch): return adc.read(ch) / 1024

stations = [
    ((88.4,89.7),'BBC Radio 2'),
    ((90.6,91.9),'BBC Radio 3'),
    ((92.8,94.1),'BBC Radio 4'),
    ((94.9,94.9),'BBC London'),
    ((95.8,95.8),'Capital FM'),
    ((97.3,97.3),'LBC'),
    ((98.0,99.3),'BBC Radio 1'),
    ((100.0,100.0),'Kiss'),
    ((100.6,100.9),'Classic FM'),
    ((105.4,105,4),'Magic'),
    ((106.2,106.2),'Heart'),
    ((107.1,107.1),'Capital XTRA')
    ]
            
def get_freq():
	# FM is 88-108 MHz
	return round(88.0 + (20.0 / _get(1)), 1)

def lookup_chan(freq):
    PAD = 0.5
    for f,n in stations:
        if f-PAD <= freq <= f+PAD:
	    return n
    return None

def speak(text):
    subprocess.Popen('espeak -ven+f2 -k5 -s150 "{}"'.format(text).split())

def sigterm_mplayer():
    pids = map(int,subprocess.check_output(['pidof','mplayer']).split())
    for p in pids:
        os.kill(p, 15)

current_chan = None

while True:
    time.sleep(0.2)

    # set volume
    subprocess.call('amixer -D pulse sset Master {}%'.format(_get(0)).split()) 

    # select station
    chan = lookup_chan(get_freq())
    if chan != current_chan:
        sigterm_mplayer()
	current_chan = chan
	if not chan:
	    subprocess.Popen('mplayer -softvol -vo null whitenoise.mp3'.split())
	else:
	    speak(chan)
	    station = stations_tunein.StationsTunein().get_station(chan)
	    station_cmd = ''
	    if station.has_key('stream_id'):
	        station_cmd += '-aid ' + station['stream_id']
	    if station.get('playlist', False) == 'yes':
	    	station_cmd += '-playlist'
	    station_cmd += station['stream']
	    subprocess.Popen('mplayer -softvol -vo null -cache 32 {}'.format(station_cmd).split())

