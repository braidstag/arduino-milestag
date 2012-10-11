#!/usr/bin/python

import argparse
import re
import socket
import serial
import sys
from threading import Thread, Lock
from Queue import Queue

from core import Player, StandardGameLogic, ClientServer
import proto

class ClientCallback():
  def playerDead(self):
    print "Out of lives!"

class Main():

  def __init__(self):
    parser = argparse.ArgumentParser(description='BraidsTag gun logic.')
    parser.add_argument('-s', '--serial', type=str, help='serial device to which the arduino is connected', required=True)
    #parser.add_argument('-p', '--playerID', type=self._stringToPlayerID, help='player id', default=1)
    #parser.add_argument('-t', '--teamID', type=int, choices=xrange(1, 8), help='team id', default=1)

    self.args = parser.parse_args()

    self.serverConnection = ServerConnection()
    self.serverConnection.start()

    try:
      self.serial = serial.Serial(self.args.serial, 115200)
      self.properSerial = True
    except serial.serialutil.SerialException:
      #Try just opening this as a file
      self.serial = open(self.args.serial)
      self.properSerial = False

    (teamID, playerID) = self.serverConnection.sendHello()
    self.player = Player(teamID, playerID)
    self.logic = StandardGameLogic(ClientCallback())

    self.connectToArduino()

  def serialWrite(self, line):
    if (self.properSerial):
      self.serial.write(line)
    else:
      print(line)

  def eventLoop(self):
    for line in self.serial:
      line = line.rstrip()

      try:
        (sentTeam, sentPlayer, damage) = proto.HIT.parse(line)

        self.logic.hit(self.player, sentTeam, sentPlayer, damage)
      except proto.MessageParseException:
        pass

      try:
        proto.TRIGGER.parse(line)

        if (self.logic.trigger(self.player)):
          self.serialWrite("Fire(%d,%d,%d)\n" % (self.player.teamID, self.player.playerID, self.player.gunDamage))
      except proto.MessageParseException:
        pass


      msg = "Recv(%s,%s,%s)\n" % (self.player.teamID, self.player.playerID, line)
      self._sendToServer(msg, "Ack()\n")

  def _stringToPlayerID(self, inp):
    out = int(inp)
    if out < 1 or out > 32:
      raise argparse.ArgumentTypeError("playerId must be between 1 and 32.")
    return out;

  def _sendToServer(self, msg, ack = None):
    "queue this packet to be sent to the server"
    self.serverConnection.queueMessage(msg, ack)
  
  def connectToArduino(self):
    self.serialWrite("ClientConnect()\n")
    line = self.serial.readline()
    if (line != "ClientConnected()\n"):
      raise RuntimeError("incorrect ack to ClientConnect(): %s" % (line))

class ServerConnection(Thread):
  def __init__(self):
    super(ServerConnection, self).__init__(group=None)
    self.setDaemon(True)
    self.name = "Server Communication Thread"
    self.queue = Queue()
    self.shouldStop = False
    self.sock = None

  def run(self):
    while not (self.queue.empty() and self.shouldStop):
      (msg, ack) = self.queue.get()
      try:
        self.sendToServer(msg, ack)
      except:
        print "Unexpected error:", sys.exc_info()[0]
        raise
        #TODO retry sending the packet 
    self._closeConnection()

  def stop(self):
    "shut this Thread down nicely. This blocks until this Thread is finished."
    self.shouldStop = True
    self.join()
  
  def queueMessage(self, msg, ack):
    self.queue.put((msg, ack))

  connLock = Lock()

  def sendToServer(self, msg, ack):
    with self.connLock:
      self._checkConnection()
      totalsent=0
      while totalsent < len(msg):
        sent = self.sock.send(msg[totalsent:])
        if sent == 0:
          #TODO handle this
          raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent

      if ack:
        recieved = ''
        #TODO: This is a rubbish method as if we don't get as much data as we expected, we will block :-(
        while len(recieved) < len(ack):
          chunk = self.sock.recv(len(ack)-len(recieved))
          if chunk == '':
            #TODO handle this
            raise RuntimeError("socket connection broken")
          recieved = recieved + chunk
        if recieved != ack:
          #TODO handle this
          raise RuntimeError("incorrect ack: %s" % recieved)

  def sendHello(self):
    msg = "Hello()\n"
    with self.connLock:
      self._checkConnection()

      totalsent=0
      while totalsent < len(msg):
        sent = self.sock.send(msg[totalsent:])
        if sent == 0:
          #TODO handle this
          raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent

      recieved = ''
      while True:
        chunk = self.sock.recv(64)
        if chunk == '':
          #TODO handle this
          raise RuntimeError("socket connection broken")
        recieved = recieved + chunk
        if recieved[-1] == '\n':
          break

      try:
        return proto.TEAMPLAYER.parse(recieved)
      except proto.MessageParseException:
        #TODO handle this
        raise RuntimeError("incorrect response to Hello(): %s" % recieved)

  def _checkConnection(self):
    if self.sock == None:
      self._openConnection()

  def _openConnection(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.connect((ClientServer.SERVER, ClientServer.PORT))

  def _closeConnection(self):
    self.sock.close()

main = Main()
print main.player
main.eventLoop()
print main.player
main.serverConnection.stop()
main.serial.close()
