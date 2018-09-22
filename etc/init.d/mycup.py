#!/usr/bin/env python
  
#lights = [1,2,3,4,5,6,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]
lights = [26,27,28,29,30,31,3,2,1,4,5,6,10,9,11,12,13,14,15,16,19,18,17,20,21,22,24,23,25]

#lights        = [1,2,3,4]
lightlevels   = [0,0,0,0]
maxlevel      = 250
maxnightlevel = 125
sleeptime     = 0.3
blocked       = False
lightlayer    = 'random'
activelight   = None
interval      = 60

# layers of light
# off     = all lights off
# night   = background lighting layer with low light level except user selected light very bright
# day     = all lights off or very dim except user selected lighting very bright
# max     = all to maximum level
# pulsate = hartbeat pulsation
# random  = random mode


import signal, serial, sys, time, math, random

from sys import stdout
from time import sleep

from daemon import runner

import SocketServer
import hashlib
import base64
import socket
import struct
import ssl
import time
import sys
import errno
import logging
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from select import select

action_time = time.time()

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
        
class HTTPRequest(BaseHTTPRequestHandler):
   def __init__(self, request_text):
      self.rfile = StringIO(request_text)
      self.raw_requestline = self.rfile.readline()
      self.error_code = self.error_message = None
      self.parse_request()
      

class WebSocket(object):

   handshakeStr = (
      "HTTP/1.1 101 Switching Protocols\r\n"
      "Upgrade: WebSocket\r\n"
      "Connection: Upgrade\r\n"
      "Sec-WebSocket-Accept: %(acceptstr)s\r\n\r\n"
   )
   
   hixiehandshakedStr = (
      "HTTP/1.1 101 WebSocket Protocol Handshake\r\n"
      "Upgrade: WebSocket\r\n"
      "Connection: Upgrade\r\n"
      "Sec-WebSocket-Origin: %(origin)s\r\n"
      "Sec-WebSocket-Location: %(type)s://%(host)s%(location)s\r\n\r\n"
   )
   
   GUIDStr = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
   
   STREAM = 0x0
   TEXT = 0x1
   BINARY = 0x2
   CLOSE = 0x8
   PING = 0x9
   PONG = 0xA

   HEADERB1 = 1
   HEADERB2 = 3
   LENGTHSHORT = 4
   LENGTHLONG = 5
   MASK = 6
   PAYLOAD = 7

   def __init__(self, server, sock, address):
      self.server = server
      self.client = sock
      self.address = address
      
      self.handshaked = False
      self.headerbuffer = ''
      self.readdraftkey = False
      self.draftkey = ''
      self.headertoread = 2048
      self.hixie76 = False
      
      self.fin = 0
      self.data = None
      self.opcode = 0
      self.hasmask = 0
      self.maskarray = None
      self.length = 0
      self.lengtharray = None
      self.index = 0
      self.request = None
      self.usingssl = False

      self.state = self.HEADERB1
   
      # restrict the size of header and payload for security reasons
      self.maxheader = 65536
      self.maxpayload = 4194304

   def close(self):
      self.client.close()
      self.state = self.HEADERB1
      self.hasmask = False
      self.handshaked = False
      self.readdraftkey = False
      self.hixie76 = False
      self.headertoread = 2048 
      self.headerbuffer = ''
      self.data = ''


   def handleMessage(self):
      pass

   def handleConnected(self):
      pass

   def handleClose(self):
      pass

   def handlePacket(self):
      # close
      if self.opcode == self.CLOSE:
         self.sendClose()
         raise Exception("received client close")
      # ping
      elif self.opcode == self.PING:
         pass
      
      # pong
      elif self.opcode == self.PONG:
         pass
      
      # data
      elif self.opcode == self.STREAM or self.opcode == self.TEXT or self.opcode == self.BINARY:
         self.handleMessage()	


   def handleData(self):		
      
      # do the HTTP header and handshake
      if self.handshaked is False:
         
         data = self.client.recv(self.headertoread)
         
         if data:
            # accumulate
            self.headerbuffer += data

            if len(self.headerbuffer) >= self.maxheader:
               raise Exception('header exceeded allowable size')

            # we need to read the entire 8 bytes of after the HTTP header, ensure we do
            if self.readdraftkey is True:
               self.draftkey += self.headerbuffer
               read = self.headertoread - len(self.headerbuffer)

               if read != 0:
                  self.headertoread = read
               else:
                  # complete hixie76 handshake
                  self.handshake_hixie76()
               
            # indicates end of HTTP header
            elif '\r\n\r\n' in self.headerbuffer:
               self.request = HTTPRequest(self.headerbuffer)
               # hixie handshake
               if self.request.headers.has_key('Sec-WebSocket-Key1'.lower()) and self.request.headers.has_key('Sec-WebSocket-Key2'.lower()):
                  # check if we have the key in our buffer
                  index = self.headerbuffer.find('\r\n\r\n') + 4
                  # determine how much of the 8 byte key we have
                  read = len(self.headerbuffer) - index
                  # do we have all the 8 bytes we need?
                  if read < 8:
                     self.headertoread = 8 - read
                     self.readdraftkey = True
                     if read > 0:
                        self.draftkey += self.headerbuffer[index:index+read]
                  
                  else:
                     # get the key
                     self.draftkey += self.headerbuffer[index:index+8]
                     # complete hixie handshake
                     self.handshake_hixie76()
                     
               # handshake rfc 6455
               elif self.request.headers.has_key('Sec-WebSocket-Key'.lower()):
                  key = self.request.headers['Sec-WebSocket-Key'.lower()]
                  hStr = self.handshakeStr % { 'acceptstr' :  base64.b64encode(hashlib.sha1(key + self.GUIDStr).digest()) }
                  self.sendBuffer(hStr)
                  self.handshaked = True
                  self.headerbuffer = ''
                  
                  try:
                     self.handleConnected()
                  except:
                     pass		
               else:
                  raise Exception('Sec-WebSocket-Key does not exist')

         # remote connection has been closed
         else:
            raise Exception("remote socket closed")
            
      # else do normal data		
      else:
         data = self.client.recv(2048)
         if data:
            for val in data:
               if self.hixie76 is False:
                  self.parseMessage(ord(val))
               else:
                  self.parseMessage_hixie76(ord(val))
         else:
            raise Exception("remote socket closed")
   


   def handshake_hixie76(self):
   
      k1 = self.request.headers['Sec-WebSocket-Key1'.lower()]
      k2 = self.request.headers['Sec-WebSocket-Key2'.lower()]

      spaces1 = k1.count(" ")
      spaces2 = k2.count(" ")
      num1 = int("".join([c for c in k1 if c.isdigit()])) / spaces1
      num2 = int("".join([c for c in k2 if c.isdigit()])) / spaces2

      key = ''
      key += struct.pack('>I', num1)
      key += struct.pack('>I', num2)
      key += self.draftkey

      typestr = 'ws'
      if self.usingssl is True:
         typestr = 'wss'

      response = self.hixiehandshakedStr % { 'type' : typestr, 'origin' : self.request.headers['Origin'.lower()], 'host' : self.request.headers['Host'.lower()], 'location' : self.request.path }

      self.sendBuffer(response)
      self.sendBuffer(hashlib.md5(key).digest())

      self.handshaked = True
      self.hixie76 = True
      self.headerbuffer = ''

      try:
         self.handleConnected()
      except:
         pass
      

   def sendClose(self):

      msg = bytearray()
      if self.hixie76 is False:
         msg.append(0x88)
         msg.append(0x00)
         self.sendBuffer(msg)
      else:
         pass

   def sendBuffer(self, buff):
      size = len(buff)
      tosend = size
      index = 0

      while tosend > 0:
         try:
            # i should be able to send a bytearray
            sent = self.client.send(str(buff[index:size]))
            if sent == 0:
               raise RuntimeError("socket connection broken")

            index += sent
            tosend -= sent

         except socket.error as e:
            # if we have full buffers then wait for them to drain and try again
            if e.errno == errno.EAGAIN:
               time.sleep(0.001)
            else:
               raise e

   
   #if s is a string then websocket TEXT is sent else BINARY
   def sendMessage(self, s):
      
      if self.hixie76 is False:

         header = bytearray()
         isString = isinstance(s, str)

         if isString is True: 
            header.append(0x81)
         else:
            header.append(0x82)

         b2 = 0		
         length = len(s)

         if length <= 125:
            b2 |= length
            header.append(b2)

         elif length >= 126 and length <= 65535:
            b2 |= 126
            header.append(b2)
            header.extend(struct.pack("!H", length))
      
         else:
            b2 |= 127
            header.append(b2)
            header.extend(struct.pack("!Q", length))

         if length > 0:
            self.sendBuffer(header + s) 
         else:
            self.sendBuffer(header)
         header = None

      else:
         msg = bytearray()			
         msg.append(0)
         if len(s) > 0:
            msg.extend(str(s).encode("UTF8"))
         msg.append(0xFF)

         self.sendBuffer(msg)
         msg = None


   def parseMessage_hixie76(self, byte):

      if self.state == self.HEADERB1:
         if byte == 0:
            self.state = self.PAYLOAD
            self.data = bytearray()

      elif self.state == self.PAYLOAD:
         if byte == 0xFF:
            self.opcode = 1
            self.length = len(self.data)
            try:
               self.handlePacket()
            finally:
               self.data = None
               self.state = self.HEADERB1
         else	:
            self.data.append(byte)
            # if length exceeds allowable size then we except and remove the connection
            if len(self.data) >= self.maxpayload:
               raise Exception('payload exceeded allowable size')


   def parseMessage(self, byte):	
      # read in the header
      if self.state == self.HEADERB1:
         # fin
         self.fin = (byte & 0x80)
         # get opcode
         self.opcode = (byte & 0x0F)
         
         self.state = self.HEADERB2
      
      elif self.state == self.HEADERB2:
         mask = byte & 0x80				
         length = byte & 0x7F
         
         if mask == 128:
            self.hasmask = True
         else:
            self.hasmask = False
         
         if length <= 125:
            self.length = length
            
            # if we have a mask we must read it
            if self.hasmask is True:
               self.maskarray = bytearray()
               self.state = self.MASK
            else:
               # if there is no mask and no payload we are done
               if self.length <= 0:
                  try:
                     self.handlePacket()
                  finally:
                     self.state = self.HEADERB1
                     self.data = None
                     
               # we have no mask and some payload
               else:
                  self.index = 0
                  self.data = bytearray()
                  self.state = self.PAYLOAD
               
         elif length == 126:
            self.lengtharray = bytearray()
            self.state = self.LENGTHSHORT
            
         elif length == 127:
            self.lengtharray = bytearray()
            self.state = self.LENGTHLONG

      
      elif self.state == self.LENGTHSHORT:
         self.lengtharray.append(byte)

         if len(self.lengtharray) > 2:
            raise Exception('short length exceeded allowable size')

         if len(self.lengtharray) == 2:
            self.length = struct.unpack_from('!H', str(self.lengtharray))[0]
            
            if self.hasmask is True:
               self.maskarray = bytearray()
               self.state = self.MASK
            else:
               # if there is no mask and no payload we are done
               if self.length <= 0:
                  try:
                     self.handlePacket()
                  finally:
                     self.state = self.HEADERB1
                     self.data = None

               # we have no mask and some payload
               else:
                  self.index = 0
                  self.data = bytearray()
                  self.state = self.PAYLOAD
         
      elif self.state == self.LENGTHLONG:

         self.lengtharray.append(byte)

         if len(self.lengtharray) > 8:
            raise Exception('long length exceeded allowable size')

         if len(self.lengtharray) == 8:
            self.length = struct.unpack_from('!Q', str(self.lengtharray))[0]

            if self.hasmask is True:
               self.maskarray = bytearray()
               self.state = self.MASK
            else:
               # if there is no mask and no payload we are done
               if self.length <= 0:
                  try:
                     self.handlePacket()
                  finally:
                     self.state = self.HEADERB1
                     self.data = None

               # we have no mask and some payload
               else:
                  self.index = 0
                  self.data = bytearray()
                  self.state = self.PAYLOAD
         
      # MASK STATE
      elif self.state == self.MASK:
         self.maskarray.append(byte)

         if len(self.maskarray) > 4:
            raise Exception('mask exceeded allowable size')

         if len(self.maskarray) == 4:
            # if there is no mask and no payload we are done
            if self.length <= 0:
               try:
                  self.handlePacket()
               finally:
                  self.state = self.HEADERB1
                  self.data = None
                  
            # we have no mask and some payload
            else:
               self.index = 0
               self.data = bytearray()
               self.state = self.PAYLOAD
      
      # PAYLOAD STATE
      elif self.state == self.PAYLOAD:
         if self.hasmask is True:
            self.data.append( byte ^ self.maskarray[self.index % 4] )
         else:
            self.data.append( byte )

         # if length exceeds allowable size then we except and remove the connection
         if len(self.data) >= self.maxpayload:
            raise Exception('payload exceeded allowable size')

         # check if we have processed length bytes; if so we are done
         if (self.index+1) == self.length:
            try:
               self.handlePacket()
            finally:
               self.state = self.HEADERB1
               self.data = None
         else:
            self.index += 1


class SimpleWebSocketServer(object):
   def __init__(self, host, port, websocketclass):
      self.websocketclass = websocketclass
      self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.serversocket.bind((host, port))
      self.serversocket.listen(5)
      self.connections = {}
      self.listeners = [self.serversocket]
      self.mydmx = None


   def decorateSocket(self, sock):
      return sock

   def constructWebSocket(self, sock, address):
      return self.websocketclass(self, sock, address)

   def close(self):
      self.serversocket.close()
   
      for conn in self.connections.itervalues():
         try:
            conn.handleClose()
         except:
            pass
   
         conn.close()

   def getTime(self):
      hour = time.localtime().tm_hour
      min = time.localtime().tm_min
      return hour, min

   def DMXoff(self):
      global blocked
      global activelight
      for i in lights:
         self.mydmx.setChannel(i, 0, autorender=False)
         if blocked and activelight == i:
            self.mydmx.setChannel(i, maxlevel, autorender=False)
            blocked = False
      self.mydmx.render()

   def DMXmax(self):
      global blocked
      global activelight
      for i in lights:
         self.mydmx.setChannel(i, maxlevel, autorender=False)
         if blocked and activelight == i:
            self.mydmx.setChannel(i, maxlevel, autorender=False)
            blocked = False
      self.mydmx.render()

   def DMXsequence(self):
      global lightlayer
      global activelight
      global blocked

      #for i in range(lights_number):
      #	self.mydmx.setChannel(i+1,0)
      #	self.mydmx.render()

      #print("MyCup DMX daemon running.")
      #for i in range(lights_number):
      #	intensity = 32*math.sin(time.time()+i)
      #	self.mydmx.setChannel(i+1,int(intensity))
      #self.mydmx.render()
      for i in lights:
      	 self.mydmx.setChannel(i,maxlevel)
         self.mydmx.render()
         time.sleep(sleeptime)
         self.mydmx.setChannel(i,0)
         self.mydmx.render()

      #for i in lights:
      #	self.mydmx.setChannel(i, 0, autorender=True)
      #self.mydmx.setChannel(int(sys.argv[1]), 255, autorender=True)

      #for i in lights:
      #   intensity = maxlevel*math.sin(time.time()+i*.001)+ (maxlevel/2)
      #   self.mydmx.setChannel(i, int(intensity), autorender=False) 
      #   if blocked and activelight == i:
      #      self.mydmx.setChannel(i, maxlevel, autorender=False)
      #      blocked = False
      #   #time.sleep(sleeptime)
      #   #self.mydmx.setChannel(i,0,autorender=True)
      #self.mydmx.render()


   def DMXcycle(self):
      global lightlayer
      global activelight
      global blocked
      step = 2

      #for i in range(lights_number):
      #	self.mydmx.setChannel(i+1,0)
      #	self.mydmx.render()

      #print("MyCup DMX daemon running.")
      #for i in range(lights_number):
      #	intensity = 32*math.sin(time.time()+i)
      #	self.mydmx.setChannel(i+1,int(intensity))
      #self.mydmx.render()
      #for i in range(lights_number):
      #	self.mydmx.setChannel(i+1,128)
      #	self.mydmx.render()
      #	time.sleep(2)
      #	self.mydmx.setChannel(i+1,0)
      #	self.mydmx.render()

      #for i in lights:
      #	self.mydmx.setChannel(i, 0, autorender=True)
      #self.mydmx.setChannel(int(sys.argv[1]), 255, autorender=True)

      #for i in lights:
      #   intensity = maxlevel*math.sin(time.time()+i*.001)+ (maxlevel/2)
      #   self.mydmx.setChannel(i, int(intensity), autorender=False) 
      #   if blocked and activelight == i:
      #      self.mydmx.setChannel(i, maxlevel, autorender=False)
      #      blocked = False
      #   #time.sleep(sleeptime)
      #   #self.mydmx.setChannel(i,0,autorender=True)
      #self.mydmx.render()

      for i in lights:
         for l in range(0,maxlevel,step):
	          self.mydmx.setChannel(i, l, autorender=True) 
         for l in range(maxlevel,0,-step):
	          self.mydmx.setChannel(i, l, autorender=True) 
            #time.sleep(sleeptime)
            #mydmx.setChannel(i,0,autorender=True)



   def DMXrandom(self):
      global lightlayer
      global activelight
      global blocked
      sleeptime = 0.0

      #for i in range(lights_number):
      #	self.mydmx.setChannel(i+1,0)
      #	self.mydmx.render()

      #print("MyCup DMX daemon running.")
      #for i in range(lights_number):
      #	intensity = 32*math.sin(time.time()+i)
      #	self.mydmx.setChannel(i+1,int(intensity))
      #self.mydmx.render()
      #for i in range(lights_number):
      #	self.mydmx.setChannel(i+1,128)
      #	self.mydmx.render()
      #	time.sleep(2)
      #	self.mydmx.setChannel(i+1,0)
      #	self.mydmx.render()

      #for i in lights:
      #	self.mydmx.setChannel(i, 0, autorender=True)
      #self.mydmx.setChannel(int(sys.argv[1]), 255, autorender=True)

      #for i in lights:
      #   intensity = maxlevel*math.sin(random.random())
      #   self.mydmx.setChannel(i, int(intensity), autorender=True) 
         #if blocked and activelight == i:
         #   self.mydmx.setChannel(i, maxlevel, autorender=True)
         #   blocked = False
         #time.sleep(sleeptime)
         #self.mydmx.setChannel(i,0,autorender=True)
      #self.mydmx.render()
      
      for i in lights:
         intensity = maxlevel*math.sin(random.random())
         self.mydmx.setChannel(i, int(intensity), autorender=True)
         time.sleep(sleeptime) 



   def DMXpulsate(self):
      global lightlayer
      global activelight
      global blocked


      for i in lights:
         intensity = maxlevel*math.sin(time.time()+i*.001)+ (maxlevel/2)
         self.mydmx.setChannel(i, int(intensity), autorender=True) 
         time.sleep(sleeptime)
         if blocked and activelight == i:
            self.mydmx.setChannel(i, maxlevel, autorender=True)
            blocked = False
         #time.sleep(sleeptime)
         #self.mydmx.setChannel(i,0,autorender=True)
      self.mydmx.render()


   def DMXsnake(self, sleeptime):
      for j in range((len(lights))):
         for i in lights:
            l = (maxlevel/2)*math.sin(time.time()*(j+maxlevel))+maxlevel/2
            self.mydmx.setChannel(i, int(l), autorender=True)
            time.sleep(sleeptime)   
            #print(l),
         #print()         
         #l = maxlevel*math.sin(j*time.time())
      
      

   def serveforever(self):
      self.mydmx = DMXConnection('/dev/ttyUSB0')
      self.DMXoff()
      global lightlayer
      global blocked
      global activelight
      global action_time
      global previous_time
      global interval
      
      
      
      while True:
      
         if (time.time() >= (action_time+interval)):
            lightlayer = 'off'

         #print lightlayer

         # layers of light
         # off     = all lights off
         # night   = background lighting layer with low light level except user selected light very bright
         # day     = all lights off or very dim except user selected lighting very bright
         # max     = all lights to maximum level
         # pulsate = hartbeat pulsation
         # random  = random mode

         if lightlayer == 'off':
            self.DMXoff()
         elif lightlayer == 'max':
            self.DMXmax()
         elif lightlayer == 'night':
            self.DMXcycle()
         elif lightlayer == 'day':
            self.DMXcycle()    
         elif lightlayer == 'pulsate':
            self.DMXpulsate()    
         elif lightlayer == 'random':
            self.DMXrandom()    
         elif lightlayer == 'sequence':
            self.DMXsequence()    
         elif lightlayer == 'candle':
            self.DMXrandom()
         elif lightlayer == 'rotate':
            self.DMXrotate()
         elif lightlayer == 'snake':
            self.DMXsnake()   
      
         rList, wList, xList = select(self.listeners, [], self.listeners, 1)	

         for ready in rList:
            if ready == self.serversocket:
               try:
                  sock, address = self.serversocket.accept()
                  newsock = self.decorateSocket(sock)
                  newsock.setblocking(0)
                  fileno = newsock.fileno()
                  self.listeners.append(fileno)
                  self.connections[fileno] = self.constructWebSocket(newsock, address)

               except Exception as n:

                  logging.debug(str(address) + ' ' + str(n))

                  if sock is not None:
                     sock.close()
            else:
               client = self.connections[ready]

               try:
                  client.handleData()

               except Exception as n:

                  logging.debug(str(client.address) + ' ' + str(n))

                  try:
                     client.handleClose()
                  except:
                     pass

                  client.close()

                  del self.connections[ready]
                  self.listeners.remove(ready)

         if lightlayer == 'off':
            self.DMXoff()
         elif lightlayer == 'max':
            self.DMXmax()
         elif lightlayer == 'night':
            self.DMXcycle()
         elif lightlayer == 'day':
            self.DMXcycle()    
         elif lightlayer == 'pulsate':
            self.DMXpulsate()    
         elif lightlayer == 'random':
            self.DMXrandom()    
         elif lightlayer == 'sequence':
            self.DMXsequence()    
         elif lightlayer == 'candle':
            self.DMXrandom()
         elif lightlayer == 'rotate':
            self.DMXrotate()
         elif lightlayer == 'snake':
            self.DMXsnake()   

      
         for failed in xList:
            if failed == self.serversocket:
               self.close()
               raise Exception("server socket failed")
            else:
               client = self.connections[failed]

               try:
                  client.handleClose()
               except:
                  pass

               client.close()

               del self.connections[failed]
               self.listeners.remove(failed)

         if lightlayer == 'off':
            self.DMXoff()
         elif lightlayer == 'max':
            self.DMXmax()
         elif lightlayer == 'night':
            self.DMXcycle()
         elif lightlayer == 'day':
            self.DMXcycle()    
         elif lightlayer == 'pulsate':
            self.DMXpulsate()    
         elif lightlayer == 'random':
            self.DMXrandom()    
         elif lightlayer == 'sequence':
            self.DMXsequence()    
         elif lightlayer == 'candle':
            self.DMXrandom()
         elif lightlayer == 'rotate':
            self.DMXrotate()
         elif lightlayer == 'snake':
            self.DMXsnake()   
               

class SimpleSSLWebSocketServer(SimpleWebSocketServer):

   def __init__(self, host, port, websocketclass, certfile, keyfile, version = ssl.PROTOCOL_TLSv1):

      SimpleWebSocketServer.__init__(self, host, port, websocketclass)

      self.cerfile = certfile
      self.keyfile = keyfile
      self.version = version

   def close(self):
      super(SimpleSSLWebSocketServer, self).close()

   def decorateSocket(self, sock):
      sslsock = ssl.wrap_socket(sock,
                           server_side=True,
                           certfile=self.cerfile,
                           keyfile=self.keyfile,
                           ssl_version=self.version)
      return sslsock

   def constructWebSocket(self, sock, address):
      ws = self.websocketclass(self, sock, address)
      ws.usingssl = True
      return ws

   def serveforever(self):
      super(SimpleSSLWebSocketServer, self).serveforever()
               
class WebSocketLight(WebSocket):
   def handleMessage(self):
      global lightlayer
      global activelight
      global blocked
      global action_time
      global previous_time
      global interval
      print self.address, self.data   
      if self.data is None:
         self.data = ''
      elif self.data == 'off':
         lightlayer = 'off'
         #print 'off'
      elif self.data == 'night':
         lightlayer = 'night'
         action_time = time.time()
      elif self.data == 'day': 
         lightlayer = 'day'
         action_time = time.time()
      elif self.data == 'max': 
         lightlayer = 'max'
         action_time = time.time()
      elif self.data == 'pulsate': 
         lightlayer = 'pulsate'
         action_time = time.time()
      elif self.data == 'random': 
         lightlayer = 'random'
         action_time = time.time()
      elif self.data == 'sequence': 
         lightlayer = 'sequence'
         action_time = time.time()
      elif self.data == 'candle': 
         lightlayer = 'candle'
         action_time = time.time()
      elif self.data == 'rotate': 
         lightlayer = 'rotate'
         action_time = time.time()
      elif self.data == 'snake': 
         lightlayer = 'snake'
         action_time = time.time()
      elif int(self.data) in lights:
         print int(self.data)
         if not blocked: 
            activelight = int(self.data)
            blocked = True
                  
      # layers of light
      # off     = all lights off
      # night   = background lighting layer with low light level except user selected light very bright
      # day     = all lights off or very dim except user selected lighting very bright
      # max     = all lights to maximum level
      # pulsate = hartbeat pulsation
      # random  = random mode
      
      #try:
      #   self.sendMessage(str(self.data))
      #except Exception as n:
      #   print n
         
   def handleConnected(self):
      print self.address, 'connected'

   def handleClose(self):
      print self.address, 'closed'
      
class App():

	def __init__(self):
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/tty0'
		self.stderr_path = '/dev/tty0'
		self.pidfile_path =  '/tmp/mycup.pid'
		self.pidfile_timeout = 5

	def run(self):
		cls = WebSocketLight
		server = SimpleWebSocketServer('', 8000, cls)

		def close_sig_handler(signal, frame):
			server.close()
			sys.exit()

		signal.signal(signal.SIGINT, close_sig_handler)
		server.serveforever()

if __name__ == "__main__":
	app = App()
	daemon_runner = runner.DaemonRunner(app)
	daemon_runner.do_action()


"""
mydmx = pysimpledmx.DMXConnection('/dev/ttyUSB0')

while True:
	for i in range(lights_number):
		intensity = 32*math.sin(time.time()+i)
		mydmx.setChannel(i+1,int(intensity))
		#print(i, int(intensity)),

        mydmx.render()
        #print()
"""



#mydmx.setChannel(1, 255) # set DMX channel 1 to full
#mydmx.setChannel(2, 128) # set DMX channel 2 to 128
#mydmx.setChannel(3, 0)   # set DMX channel 3 to 0
#mydmx.render()    # render all of the above changes onto the DMX network

#mydmx.setChannel(4, 255, autorender=True) # set channel 4 to full and render to the network

"""
import sys
from dmx import *
import math

#port = sys.argv[1]
port = '/dev/ttyUSB0'
manager = DMXManager(port)
lights = []

for i in range(lights_number):
	print(i)
	lights.append(DMXDevice(start=i, length=2))
	manager.append(lights[i])

print(lights)
for light in lights:
	print(light.values),
print()
print()

#light_0 = DMXDevice(start=0, length=2)
#light_1 = DMXDevice(start=2, length=2)
#manager.append(light_0)
#manager.append(light_1)

while True:
	for i in range(len(lights)):
		intensity = 128*math.sin(time.time()+i)+128
		#light.set(0,int(intensity))
		lights[i].set(1,int(intensity))
		print(lights[i].start, lights[i].values),

	#light_0.set(0, int(intensity))
	#light_1.set(1, int(intensity))
	
	#for light in light_0, light_1:
	#  for color in range(3):
	#    light.set(color, random.randintil.com(0, 255))

	manager.send()
	print()

"""

"""
def one_by_one(step):
   for i in lights:
      for l in range(0,maxlevel,step):
	       mydmx.setChannel(i, l, autorender=True) 
      for l in range(maxlevel,0,-step):
	       mydmx.setChannel(i, l, autorender=True) 
         #time.sleep(sleeptime)
         #mydmx.setChannel(i,0,autorender=True)

def light_snake(sleeptime):
   for j in range((len(lights))):
      for i in lights:
         l = (maxlevel/2)*math.sin(time.time()*(j+maxlevel))+maxlevel/2
         mydmx.setChannel(i, int(l), autorender=True)
         time.sleep(sleeptime)   
         #print(l),
      #print()         
      #l = maxlevel*math.sin(j*time.time())
      
      
def sequence():
   for i in lights:
      mydmx.setChannel(i,maxlevel)
      mydmx.render()
      time.sleep(sleeptime)
      mydmx.setChannel(i,0)
      mydmx.render()

def cycle():
   for i in lights:
      intensity = maxlevel*math.sin(time.time()+i*.001)+ (maxlevel/2)
      mydmx.setChannel(i, int(intensity), autorender=False) 
      mydmx.render()

def random_light(sleeptime):
   for i in lights:
      intensity = maxlevel*math.sin(random.random())
      mydmx.setChannel(i, int(intensity), autorender=True)
      time.sleep(sleeptime) 

def rotate(sleeptime):
   for i in lights:
      intensity = maxlevel*math.sin(time.time()+i*.001)+ (maxlevel/2)
      mydmx.setChannel(i, int(intensity), autorender=True) 
      time.sleep(sleeptime)
   #self.mydmx.render()

"""
