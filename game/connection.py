import socket
import sys
from threading import Thread, Lock
import Queue

from core import ClientServer

class ClientServerConnection():
  def __init__(self):
    self.sock = None
    self.readThread = None
    self.writeThread = WriteThread()
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
    raise RuntimeError("onDisconnectCalled")
    #TODO: support this
    
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
      if chunk == '':
        if self.shouldStop:
          #this is expected
          return
        self.parent.onDisconnect()
      recieved = recieved + chunk

      (partial, complete) = self._takeCompleteResponses(recieved)
      recieved = partial

      for i in complete:
        #TODO: actually track these
        if i == "Ack()\n":
          continue

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
  def __init__(self):
    super(WriteThread, self).__init__(group=None)
    self.setDaemon(True)
    self.name = "Client/Server Write Thread"
    self.sock = None # this will be set by setSocket
    self.queue = Queue.Queue()
    self.shouldStop = False

  def run(self):
    while not (self.queue.empty() and self.shouldStop):
      try:
        msg = self.queue.get(True, 5) + "\n"
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
    self.queue.put(msg)

  def setSocket(self, sock):
    self.sock = sock

