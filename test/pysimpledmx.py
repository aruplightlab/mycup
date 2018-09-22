#!/usr/bin/env python

import serial, sys, time

START_VAL = 0x7E
END_VAL = 0xE7

COM_BAUD = 57600
COM_TIMEOUT = 1
COM_PORT = '/dev/ttyUSB0'

LABELS = {     
               'GET_WIDGET_PARAMETERS' :3,  #unused
               'SET_WIDGET_PARAMETERS' :4,  #unused
               'RX_DMX_PACKET'         :5,  #unused
               'TX_DMX_PACKET'         :6,
               'TX_RDM_PACKET_REQUEST' :7,  #unused
               'RX_DMX_ON_CHANGE'      :8,  #unused
          }
          
          
class DMXConnection(object):
    
    def __init__(self, comport=None):
        
        self.com = 0
        self.dmx_frame = list()
        
      #setup channel output list
        for i in xrange (513):
            self.dmx_frame.append(0)

        try:
            self.com = serial.Serial(comport, baudrate=COM_BAUD, timeout=COM_TIMEOUT)
        except:
            print "Could not open COM%s, quitting application" % (port_num+1)
            sys.exit(0)
            
        print "Opened %s" % (self.com.portstr)

    
    def setChannel(self, chan, val, autorender=False):
    #  takes channel and value arguments to set a channel level in the local 
    #  dmx frame, to be rendered the next time the render() method is called
        if (chan > 512) or (chan < 1):
            print "invalid channel"
            return
        if val > 255: val=255
        if val < 0: val=0
        self.dmx_frame[chan] = val
        if autorender:
            self.render()
    
    def clear(self, chan=0):
    #  clears all channels to zero. blackout.
    #  with optional channel argument, clears only one channel
        if chan==0:
            for i in xrange (1, 512, 1):
                self.dmx_frame[i]=0
        else:
            self.dmx_frame[chan]=0
            
    
    def render(self):
    #  updates the dmx output from the USB DMX Pro with the values from self.dmx_frame
        packet = []
        packet.append(chr(START_VAL))
        packet.append(chr(LABELS['TX_DMX_PACKET']))
        packet.append(chr(len(self.dmx_frame) & 0xFF))
        packet.append(chr((len(self.dmx_frame) >> 8) & 0xFF))
        
        for j in xrange(len(self.dmx_frame)):
            packet.append(chr(self.dmx_frame[j]))
            
        packet.append(chr(END_VAL))
        
        self.com.write(''.join(packet)) 
        
    def close(self):
        self.com.close()
        
mydmx = DMXConnection('/dev/ttyUSB0')
      
#mydmx.setChannel(1, 255) # set DMX channel 1 to full
#mydmx.setChannel(2, 128) # set DMX channel 2 to 128
#mydmx.setChannel(3, 0)   # set DMX channel 3 to 0
#mydmx.render()    # render all of the above changes onto the DMX network

maxlevel  = 250
sleeptime = 0.2

#lights = [1,2,3,4]
#lights = [1,2,3,4,5,6,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]
lights = [26,27,28,29,30,31,3,2,1,4,5,6,10,9,11,12,13,14,15,16,19,18,17,20,21,22,24,23,25]


for i in lights:
        mydmx.setChannel(i, 0, autorender=True)
 
#mydmx.setChannel(int(sys.argv[1]), 255, autorender=True)

while True:
	for i in lights:
		mydmx.setChannel(i, maxlevel, autorender=True) 
		time.sleep(sleeptime)
		mydmx.setChannel(i,0,autorender=True)
