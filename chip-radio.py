# Next Thing Co. C.H.I.P-based internet radio build
# @depletionmode, 2016
# 
# Dependancies:
#  * https://github.com/xtacocorex/CHIP_IO
#  * https://github.com/xtacocorex/Adafruit_Python_GPIO
#  * Adafruit_MCP3008 (https://github.com/adafruit/Adafruit_Python_MCP3008)

import os
import time
import subprocess

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008 as ADC

adc = ADC.MCP3008(spi=SPI.SpiDev(32766, 0))

def _adc_ave_read(n, samples=1000):
    v = 0
    for i in range(samples):
        v += adc.read_adc(n)
    v /= samples
    return v

def _is_on():
    if _adc_ave_read(3) > 500:
        return True
    return False

stations = [
    ((88.4,90.0),'BBC Radio 2','http://www.radiofeeds.co.uk/bbcradio2.pls'),
    ((90.0,92.0),'BBC Radio 3','http://www.radiofeeds.co.uk/bbcradio3.pls'),
    ((92.0,94.0),'BBC Radio 4','http://www.radiofeeds.co.uk/bbcradio4.pls'),
    ((94.0,96.0),'BBC London','http://www.radiofeeds.co.uk/bbclondon.pls'),
    ((96.0,97.5),'Capital London','http://media-ice.musicradio.com/CapitalMP3.m3u'),
    ((98.0,99.5),'BBC Radio 1','http://www.radiofeeds.co.uk/bbcradio1.pls'),
    ((100.0,102.0),'Kiss','http://tx.whatson.com/icecast.php?i=kiss100.mp3.m3u'),
    ((104.0,106),'Magic','http://media-ice.musicradio.com/HeartLondonMP3.m3u'),
    ((106.0,107.5),'Heart','http://media-ice.musicradio.com/HeartLondonMP3.m3u'),
    ]
            
def get_freq():
    # FM is 88-108 MHz
    freq_step_list = [0,12,38,45,65,80,105,130,160,185,205,245,275,310,360,400,455,520,590,690,770]
    # sample multiple times
    v = _adc_ave_read(0, 5000)
    # find bucket
    TILT=0
    for i in range(len(freq_step_list)-1):
        if freq_step_list[i]+TILT <= v <= freq_step_list[i+1]+TILT:
            return 88.0 + i
    return 108.0

def lookup_chan(freq):
    PAD = 0
    for f,n,s in stations:
        if f[0]-PAD <= freq < f[1]+PAD:
	    return n,s
    return None,None

def speak(text):
    subprocess.Popen('mplayer {}.wav'.format(text.replace(' ','_')).split())
    #subprocess.call('flite -t "Station {}" -voice slt'.format(text).split())
    #subprocess.call('espeak -ven+f3 -k5 -s150 "Station {}"'.format(text).split())

def sigterm_mplayer():
    try:
        pids = map(int,subprocess.check_output(['pidof','mplayer']).split())
        for p in pids:
            os.kill(p, 15)
    except:
        pass

current_chan = "Niks nie"
current_vol = 0

while True:
    time.sleep(0.7)
    
    if not _is_on():
        sigterm_mplayer()
        current_chan = "Niks nie"
        current_vol = 0
        continue

    # set volume
    vol = int(100*_adc_ave_read(1,100)/1024.0)
    if vol >= current_vol + 3 or vol <= current_vol - 3:
        current_vol = vol
        print "vol:", vol
        subprocess.call(['amixer','sset','\'Power Amplifier\'','{}%'.format(vol)])

    # select station
    freq = get_freq()
    chan = lookup_chan(freq)
    print "freq:", freq
    if chan[0] != current_chan:
        current_chan_time = 0
	if not chan[0] and current_chan != None:
            pass
            #sigterm_mplayer()
	    #subprocess.Popen('mplayer -quiet -vo null whitenoise.mp3'.split())
	else:
            sigterm_mplayer()
            print 'Turning to', chan[0]
	    speak(chan[0])
            time.sleep(1)
	    subprocess.Popen('mplayer -quiet -vo null -cache 32 -playlist {}'.format(chan[1]).split())
	current_chan = chan[0]

