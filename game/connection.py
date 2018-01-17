import socket
import sys
import time
from threading import Thread, Lock
import Queue

from core import ClientServer
from proto import Event

class PiSerialIdProvider():
  """ An IdProvider which uses the serial number of the CPU (i.e. of the Pi) or, failing that, a random number"""
  def __init__(self):
    self.clientId = None

    # Try to extract serial from cpuinfo file
    try:
      f = open('/proc/cpuinfo','r')
      for line in f:
        if line[0:6]=='Serial':
          self.clientId = long(line[10:26], 16)
      f.close()
    except:
      pass

    #Fallback to a random number
    if not self.clientId:
      import random
      self.clientId = random.getrandbits(64)

  def __call__(self):
    return self.clientId


class ClientServerConnection():
  def __init__(self, idProvider = PiSerialIdProvider(), timeProvider = time.time):
    self.sock = None
    self.readThread = None
    self.writeThread = WriteThread(idProvider, timeProvider)
    self.writeThread.start()

  def queueMessage(self, msg):
    print "-->", repr(msg)
    sys.stdout.flush()

    self.writeThread.queueMessage(msg)

  def setSocket(self, sock):
    self.sock = sock

    #clean up old thread
    if self.readThread:
      self.readThread.stop()

    #start new one
    self.readThread = ReadThread(self.sock, self)
    self.readThread.start()

    self.writeThread.setSocket(self.sock)

  def _closeConnection(self):
    if self.sock:
      self.sock.shutdown(2)
      self.sock.close()
      self.sock = None

  def onDisconnect(self):
    "Called when this connection is disconnected. Should be overridden in subclasses"
    raise RuntimeError("onDisconnectCalled")
    
  def stop(self):
    self.writeThread.stop()
    self.readThread.stop()
    self._closeConnection()

class ReadThread(Thread):
  def __init__(self, sock, parent):
    super(ReadThread, self).__init__(group=None)
    self.setDaemon(True)
    self.name = "Client/Server Read Thread"
    self.sock = sock
    self.parent = parent
    self.shouldStop = False

  def run(self):
    recieved = ''
    chunk = ''
    while True:
      try:
        chunk = self.sock.recv(1024)
      except socket.timeout:
        if self.shouldStop:
          #this is expected
          return
        continue
      except socket.error as e:
        if self.shouldStop:
          #this is expected
          return
        print e
        self.parent.onDisconnect()
        break
      if chunk == '':
        if self.shouldStop:
          #this is expected
          return
        self.parent.onDisconnect()
        break
      recieved = recieved + chunk

      (partial, complete) = self._takeCompleteResponses(recieved)
      recieved = partial

      for i in complete:
        print "<--", repr(i)
        sys.stdout.flush()

        if self.parent.handleMsg(i):
          continue
        else:
          raise RuntimeError("Received unknown message: %s" % i)

  def _takeCompleteResponses(self, recieved):
    """Extract complete responses from a char stream.
       return a tuple containing the remaining partial response and a list of complete responses
    """
    allResp = recieved.split('\n')
    partial = allResp.pop(-1)

    return (partial, allResp)

  def stop(self):
    self.shouldStop = True

class WriteThread(Thread):
  def __init__(self, idProvider, timeProvider):
    super(WriteThread, self).__init__(group=None)
    self.setDaemon(True)
    self.name = "Client/Server Write Thread"
    self.sock = None # this will be set by setSocket
    self.queue = Queue.Queue()
    self.shouldStop = False

    self.idProvider = idProvider
    self.timeProvider = timeProvider

  def run(self):
    while not (self.shouldStop and self.queue.empty()):
      try:
        msg = self.queue.get(True, 5).toStr() + "\n"
      except Queue.Empty:
        #timeout, go back round the loop to see if we should be stopping.
        continue
      try:
        totalsent=0
        while totalsent < len(msg):
          sent = self.sock.send(msg[totalsent:])
          if sent == 0:
            #NB. we should rely on the readThread to signal a closed connection
            #TODO handle this
            raise RuntimeError("socket connection broken")
          totalsent = totalsent + sent
      except:
        print "Unexpected error:", sys.exc_info()[0]
        raise
        #TODO retry sending the packet 

  def stop(self):
    "shut the client server connection down nicely. This blocks until shutdown is finished."
    self.shouldStop = True
    self.join()
  
  def queueMessage(self, msg):
    self.queue.put(Event(msg, self.idProvider(), self.timeProvider()))

  def setSocket(self, sock):
    self.sock = sock
