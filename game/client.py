#!/usr/bin/python

import argparse
import serial
import sys
import time

from core import Player, StandardGameLogic, ClientServer
from connection import ClientServerConnection
import proto

class ClientCallback():
  def playerDead(self):
    print "Out of lives!"

class Client(ClientServerConnection):
  def __init__(self, main):
    ClientServerConnection.__init__(self)
    self.main = main
  def handleMsg(self, msg):
    try:
      (teamID, playerID) = proto.TEAMPLAYER.parse(msg)
      self.main.player = Player(teamID, playerID)
      return True
    except proto.MessageParseException:
      pass
    
    return False


class Main():

  def __init__(self):
    parser = argparse.ArgumentParser(description='BraidsTag gun logic.')
    parser.add_argument('-s', '--serial', type=str, help='serial device to which the arduino is connected', required=True)
    #parser.add_argument('-p', '--playerID', type=self._stringToPlayerID, help='player id', default=1)
    #parser.add_argument('-t', '--teamID', type=int, choices=xrange(1, 8), help='team id', default=1)

    self.args = parser.parse_args()

    self.serverConnection = Client(self)
    self._sendToServer("Hello()\n")

    try:
      self.serial = serial.Serial(self.args.serial, 115200)
      self.properSerial = True
    except serial.serialutil.SerialException:
      #Try just opening this as a file
      self.serial = open(self.args.serial)
      self.properSerial = False

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
      self._sendToServer(msg)

  def _stringToPlayerID(self, inp):
    out = int(inp)
    if out < 1 or out > 32:
      raise argparse.ArgumentTypeError("playerId must be between 1 and 32.")
    return out;

  def _sendToServer(self, msg):
    "queue this packet to be sent to the server"
    self.serverConnection.queueMessage(msg)
  
  def connectToArduino(self):
    self.serialWrite("ClientConnect()\n")
    line = self.serial.readline()
    if (line != "ClientConnected()\n"):
      raise RuntimeError("incorrect ack to ClientConnect(): %s" % (line))


main = Main()
print main.player
main.eventLoop()
print main.player
main.serverConnection.stop()
main.serial.close()
