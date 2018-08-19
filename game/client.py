#!/usr/bin/python

from __future__ import print_function

import argparse
import socket
import sys
import time
from threading import Thread

from core import Player, StandardGameLogic, ClientServer, GameState
from connection import ClientServerConnection
import proto


class Client(ClientServerConnection):
  def __init__(self, main, *args, **kwargs):
    ClientServerConnection.__init__(self, *args, **kwargs)
    self.main = main
    self.retryCount = 0
    
    self._openConnection()
  
  def handleMsg(self, fullLine):
    event = proto.parseEvent(fullLine)
    msgStr = event.msgStr

    h = proto.MessageHandler()

    @h.handles(proto.TEAMPLAYER)
    def teamPlayer(teamID, playerID): # pylint: disable=W0612
      self.main.setPlayer(Player(teamID, playerID))
      
    @h.handles(proto.STARTGAME)
    def startGame(duration): # pylint: disable=W0612
      self.main.gameState.setGameTime(int(duration))
      self.main.gameState.startGame()
    
    @h.handles(proto.STOPGAME)
    def stopGame(): # pylint: disable=W0612
      self.main.gameState.stopGame()
    
    @h.handles(proto.DELETED)
    def deleted(): # pylint: disable=W0612
      #just treat this as the game stopping for us.
      self.main.gameState.stopGame()
      #then shutdown as the server won't want us back.
      self.main.shutdown()
    
    @h.handles(proto.RESETGAME)
    def resetGame(): # pylint: disable=W0612
      self.main.player.reset()
    
    @h.handles(proto.PING)
    def ping(): # pylint: disable=W0612
      self.queueMessage(proto.PONG.create(event.time, 0))
          
    @h.handles(proto.PONG)
    def pong(startTime, reply): # pylint: disable=W0612
      if int(reply):
        self.queueMessage(proto.PONG.create(event.time, 0))

    return h.handle(msgStr)

  def _openConnection(self):
    try:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      #reduce the timeout while we are testing on a good network.
      #This will want increasing dramatically when we are on the wireless mesh.
      self.sock.settimeout(1)
      print("Connecting to " + ClientServer.SERVER + ":" + str(ClientServer.PORT))
      self.sock.connect((ClientServer.SERVER, ClientServer.PORT))

      self.setSocket(self.sock)
    except socket.error:
      self.onDisconnect()

  def onDisconnect(self):
    self.retryCount = self.retryCount + 1

    # retry with an exponential backoff, from 2 seconds to 32s
    # 2, 4, 8, 16, 32 = 62 + 60 * 32 = 33:02
    if (self.retryCount >= 65):
      super.onDisconnect()
      return

    if self.retryCount > 6 :
      waitTime = 64 + 32 * (self.retryCount - 6)
    else:
      waitTime = 2 * 2 ** (self.retryCount - 1)
    print("Disconnected from server, waiting " + str(waitTime) + " seconds to try again")
    sys.stdout.flush()
    time.sleep(waitTime)

    self._openConnection()

class ArgumentError(Exception):
  pass


class Main():

  def __init__(self, serial = None):
    parser = argparse.ArgumentParser(description='BraidsTag gun logic.')
    parser.add_argument('-s', '--serial', type=str, help='serial device to which the arduino is connected')

    self.args = parser.parse_args()

    self.player = None
    self.logic = StandardGameLogic()
    self.gameState = GameState()

    self.serverConnection = Client(self)
    self._sendToServer(proto.HELLO.create())

    if serial:
      self.serial = serial
      self.responsiveSerial = True
    else:
      if not self.args.serial:
        raise ArgumentError("You must specify -s if you do not start in fakeGun mode")

      try:
        import serial
        self.serial = serial.Serial(self.args.serial, 115200)
        self.responsiveSerial = True
      except ImportError:
        #We'll have to open this as a file
        print("WARNING: No serial module, assuming the serial argument is a normal file for testing")
        self.serial = open(self.args.serial)
        self.responsiveSerial = False
      except serial.serialutil.SerialException:
        #Try just opening this as a file
        self.serial = open(self.args.serial)
        self.responsiveSerial = False

    self.connectToArduino()

  def setPlayer(self, player):
    self.player = player

  def serialWrite(self, line):
    if (self.responsiveSerial):
      self.serial.write(line + "\n")

    print("-a>", repr(line + "\n"))
    sys.stdout.flush()

  def eventLoop(self):
    for line in self.serial:
      line = line.rstrip()
      print("<a-", repr(line))
      sys.stdout.flush()

      h = proto.MessageHandler()

      @h.handles(proto.HIT)
      def hit(sentTeam, sentPlayer, damage): # pylint: disable=W0612
        self.logic.hit(self.gameState, self.player, Player(sentTeam, sentPlayer), damage)
        return True

      @h.handles(proto.FULL_AMMO)
      def fullAmmo(): # pylint: disable=W0612
        self.logic.fullAmmo(self.gameState, self.player)
        return True

      @h.handles(proto.TRIGGER)
      def trigger(): # pylint: disable=W0612
        if (self.player and self.logic.trigger(self.gameState, self.player)):
          self.serialWrite(proto.FIRE.create(self.player.teamID, self.player.playerID, self.player.gunDamage))
        return True

      #TODO be more discerning about unparseable input here.
      h.handle(line)

      if (self.player):
        msg = proto.RECV.create(self.player.teamID, self.player.playerID, line)
      else:
        msg = proto.RECV.create(0, 0, line)
      self._sendToServer(msg)

  def _sendToServer(self, msg):
    "queue this packet to be sent to the server"
    self.serverConnection.queueMessage(msg)
  
  def connectToArduino(self):
    self.serialWrite(proto.CLIENTCONNECT.create())
    line = self.serial.readline()
    print("<a-", repr(line))
    sys.stdout.flush()

    if not proto.CLIENT_CONNECTED.parse(line):
      raise RuntimeError("incorrect ack to ClientConnect(): %s" % (line))

  def shutdown(self):
    #TODO: is this the right message for this?
    self.serialWrite(proto.CLIENTCONNECT.create())

if __name__ == "__main__":
  main = Main()
  main.eventLoop()

  print(main.player)
  main.serverConnection.stop()
  main.serial.close()
