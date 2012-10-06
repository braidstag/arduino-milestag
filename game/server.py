#!/usr/bin/python

import argparse
import socket
import sys
from threading import Thread, Lock

from core import Player, StandardGameLogic, ClientServer
from ui import MainWindow
import proto

from PySide.QtGui import QApplication

class ListeningThread(Thread):

  def __init__(self):
    super(ListeningThread, self).__init__(group=None)
    parser = argparse.ArgumentParser(description='BraidsTag server.')
    self.args = parser.parse_args()
    self.setDaemon(True)

    self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #self.serversocket.bind((socket.gethostname(), ClientServer.PORT))
    self.serversocket.bind((ClientServer.SERVER, ClientServer.PORT))
    self.serversocket.listen(5)

  def run(self):
    #start serving
    while True:
      try:
        (clientsocket, address) = self.serversocket.accept();
      except KeyboardInterrupt:
        break;
      ct = ClientThread(clientsocket)
      ct.start()

IDEAL_TEAM_COUNT=2

class GameState():
  players = {}
  teamCount = 0
  largestTeam = 0
  
  def _get_players(self):
    return self.players

  def getOrCreatePlayer(self, sentTeamStr, sentPlayerStr):
    sentTeam = int(sentTeamStr)
    sentPlayer = int(sentPlayerStr)

    if not (sentTeam, sentPlayer) in self.players:
      print "found new player %s:%s" % (sentTeam, sentPlayer)
      self.players[(sentTeam, sentPlayer)] = Player(sentTeam, sentPlayer)
      if sentTeam > self.teamCount:
        self.teamCount = sentTeam
      if sentPlayer > self.largestTeam:
        self.largestTeam = sentPlayer

      mainWindow.playerAdded(sentTeam, sentPlayer);
    return self.players[(sentTeam, sentPlayer)]

  def createNewPlayer(self):
    for playerID in range(1,32):
      for teamID in range(1,IDEAL_TEAM_COUNT + 1):
        if (teamID, playerID) not in self.players:
          return self.getOrCreatePlayer(teamID, playerID)
    #TODO handle this
    raise RuntimeError("too many players")
    
class ClientThread(Thread):
  gameState = GameState()

  def __init__(self, sock):
    super(ClientThread, self).__init__(group=None)
    self.sock = sock
    self.logic = StandardGameLogic()

  def run(self):
    #keep reading from the socket until we have it all
    msg = ''
    while True:
      chunk = self.sock.recv(1024)
      msg = msg + chunk
      if chunk == '':
        break

    ackMsg = self.handleEvent(msg)

    totalsent=0
    while totalsent < len(ackMsg):
      sent = self.sock.send(ackMsg[totalsent:])
      if sent == 0:
        #TODO handle this
        raise RuntimeError("socket connection broken")
      totalsent = totalsent + sent

  eventLock = Lock()
    
  def handleEvent(self, fullLine):
    with self.eventLock:
      print fullLine
      sys.stdout.flush()
  
    try:
      (recvTeam, recvPlayer, line) = proto.RECV.parse(fullLine)

      try:
        (sentTeam, sentPlayer, damage) = proto.HIT.parse(line)

        with self.eventLock:
          player = self.gameState.getOrCreatePlayer(recvTeam, recvPlayer)
          self.logic.hit(player, sentTeam, sentPlayer, damage)
          mainWindow.playerUpdated(recvTeam, recvPlayer)
      except proto.MessageParseException:
        pass

      try:
        proto.TRIGGER.parse(line)

        with self.eventLock:
          player = self.gameState.getOrCreatePlayer(recvTeam, recvPlayer)
          if (self.logic.trigger(player)):
            mainWindow.playerUpdated(recvTeam, recvPlayer)
#            self.logic.hit(player, fromTeam, fromPlayer, damage)
      except proto.MessageParseException:
        pass

    except proto.MessageParseException:
      pass

    try:
      proto.HELLO.parse(fullLine)

      with self.eventLock:
        player = self.gameState.createNewPlayer()
        return "TeamPlayer(%s,%s)" % (player.teamID, player.playerID)
    except proto.MessageParseException:
      pass

    return "Ack()"

main = ListeningThread()
main.start()

# Create Qt application
app = QApplication(sys.argv)
mainWindow = MainWindow(ClientThread.gameState)
mainWindow.show()

# Enter Qt main loop
retval = app.exec_()

for i in ClientThread.gameState.players.values():
  print i
sys.exit(retval)
