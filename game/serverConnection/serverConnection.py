#!/usr/bin/python

from __future__ import print_function

#TODO replace timeProvider with just time.time
#import time

from core import ClientServer
from connection import ClientServerConnection

class ServerConnection(ClientServerConnection):
  """A connection from a client to the server. There are many instances of this class, 1 for each connection"""
  outOfContactTime = 120

  def __init__(self, sock, listeningThread, msgHandler):
    ClientServerConnection.__init__(self)
    self.listeningThread = listeningThread #TODO: Can we remove this reference?
    self.msgHandler = msgHandler
    self.lastContact = self.timeProvider()
    self.latency = 0
    self.clientClockDrift = 0

    self.setSocket(sock)

  def handleMsg(self, fullLine):
    eventTime = self.msgHandler.handleMsg(fullLine, self)

    self.lastContact = eventTime
    self.listeningThread.considerMovingConfidencePoint(eventTime)

    return eventTime

  def onDisconnect(self):
    #not much we can do until they reconnect apart from note the disconnection
    print("a client disconnected")
    self.listeningThread.lostConnection(self)
    self.lastContact = -1

  def setSocket(self, sock):
    super(ServerConnection, self).setSocket(sock)
    self.startLatencyCheck()

  def isOutOfContact(self):
    return self.lastContact < self.timeProvider() - self.outOfContactTime

  def outOfContactTimeStr(self):
    return "{:,}s".format((self.timeProvider() - self.lastContact))

  def setLatency(self, latency):
    self.latency = latency

  def setClientClockDrift(self, drift):
    """Set the difference between the client and server clocks.
       A positive drift means the client is ahead of the server"""
    self.clientClockDrift = drift

  def clientTimeToServer(self, clientTime):
    return clientTime