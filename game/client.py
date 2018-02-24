#!/usr/bin/python

import argparse
import socket
import sys
import time

from core import Player, StandardGameLogic, ClientServer, GameState
from connection import ClientServerConnection
import proto

class Client(ClientServerConnection):
  def __init__(self, main, *args, **kwargs):
    ClientServerConnection.__init__(self, *args, **kwargs)
    self.main = main
    self.retryCount = 0;
    
    self._openConnection()
  
  def handleMsg(self, fullLine):
    event = proto.parseEvent(fullLine)
    msgStr = event.msgStr

    h = proto.MessageHandler()

    @h.handles(proto.TEAMPLAYER)
    def teamPlayer(teamID, playerID):
      self.main.setPlayer(Player(teamID, playerID))
      
    @h.handles(proto.STARTGAME)
    def startGame(duration):
      self.main.gameState.setGameTime(int(duration))
      self.main.gameState.startGame()
    
    @h.handles(proto.STOPGAME)
    def stopGame():
      self.main.gameState.stopGame()
    
    @h.handles(proto.DELETED)
    def deleted():
      #just treat this as the game stopping for us.
      self.main.gameState.stopGame()
      #then shutdown as the server won't want us back.
      self.main.shutdown()
    
    @h.handles(proto.RESETGAME)
    def resetGame():
      self.main.player.reset()
    
    @h.handles(proto.PING)
    def ping():
      self.queueMessage(proto.PONG.create(event.time, 1))
          
    @h.handles(proto.PONG)
    def pong(startTime, reply):
      now = self.timeProvider()
      latency = (int(startTime) - now) / 2 #TODO, do something with this.
      if reply:
        self.queueMessage(proto.PONG.create(event.time, 0))
    
    return h.handle(msgStr)

  def _openConnection(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #reduce the timeout while we are testing on a good network.
    #This will want increasing dramatically when we are on the wireless mesh.
    self.sock.settimeout(1)
    print "Connecting to " + ClientServer.SERVER + ":" + str(ClientServer.PORT)
    self.sock.connect((ClientServer.SERVER, ClientServer.PORT))

    self.setSocket(self.sock)

  def onDisconnect(self):
    self.retryCount = self.retryCount + 1

    # retry with an exponential backoff, starting at 2 seconds and
    # stopping after waiting 128s (total time 4m14s) 
    if (this.retryCount >= 5):
      super.onDisconnect()
      return
    
    time.sleep(2 * 2 ** (self.retryCount - 1))

    self._openConnection()

class ArgumentError(Exception):
  pass


class Main():

  def __init__(self):
    parser = argparse.ArgumentParser(description='BraidsTag gun logic.')
    parser.add_argument('-s', '--serial', type=str, help='serial device to which the arduino is connected')
    #parser.add_argument('-p', '--playerID', type=self._stringToPlayerID, help='player id', default=1)
    #parser.add_argument('-t', '--teamID', type=int, choices=xrange(1, 8), help='team id', default=1)
    parser.add_argument('-d', '--debugGun', help='use the debuggin gun UI', default=False, action='store_true')

    self.args = parser.parse_args()

    self.player = None

    self.serverConnection = Client(self)
    self._sendToServer(proto.HELLO.create())

    if self.args.debugGun:
      import fakeGun
      self.serial = fakeGun.showUI()
      self.responsiveSerial = True
    else:
      if not self.args.serial:
        raise ArgumentError("You must specify -s if you do not specify -d")

      try:
        import serial
        self.serial = serial.Serial(self.args.serial, 115200)
        self.responsiveSerial = True
      except ImportError:
        #We'll have to open this as a file
        print "WARNING: No serial module, assuming the serial argument is a normal file for testing"
        self.serial = open(self.args.serial)
        self.responsiveSerial = False
      except serial.serialutil.SerialException:
        #Try just opening this as a file
        self.serial = open(self.args.serial)
        self.responsiveSerial = False

    self.logic = StandardGameLogic()
    self.gameState = GameState()

    self.connectToArduino()

  def setPlayer(self, player):
    self.player = player
    
    def playerDead():
      print "Out of lives!"

    self.player.playerDead.connect(playerDead)

  def serialWrite(self, line):
    if (self.responsiveSerial):
      self.serial.write(line + "\n")

    print "-a>", repr(line + "\n")
    sys.stdout.flush()

  def eventLoop(self):
    for line in self.serial:
      line = line.rstrip()
      print "<a-", repr(line)
      sys.stdout.flush()

      h = proto.MessageHandler()

      @h.handles(proto.HIT)
      def hit(sentTeam, sentPlayer, damage):
        self.logic.hit(self.gameState, self.player, sentTeam, sentPlayer, damage)
        return True

      @h.handles(proto.FULL_AMMO)
      def fullAmmo():
        self.logic.fullAmmo(self.gameState, self.player)
        return True

      @h.handles(proto.TRIGGER)
      def trigger():
        if (self.player and self.logic.trigger(self.gameState, self.player)):
          self.serialWrite(proto.FIRE.create(self.player.teamID, self.player.playerID, self.player.gunDamage))
        return True

      #TODO be more discerning about unparseable input here.
      h.handle(line)

      if (self.player):
        msg = proto.RECV.create(self.player.teamID, self.player.playerID, line)
      else:
        msg = proto.RECV.create('', '', line)
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
    self.serialWrite(proto.CLIENTCONNECT.create())
    line = self.serial.readline()
    print "<a-", repr(line)
    sys.stdout.flush()

    if not proto.CLIENT_CONNECTED.parse(line):
      raise RuntimeError("incorrect ack to ClientConnect(): %s" % (line))

  def shutdown(self):
    self.serialWrite(proto.CLIENTCONNECT.create())

if __name__ == "__main__":
  main = Main()
  try:
    print main.player
  except:
    pass
  main.eventLoop()
  print main.player
  main.serverConnection.stop()
  main.serial.close()
