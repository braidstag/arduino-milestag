#!/usr/bin/python

import argparse
import re
import socket
import sys
from threading import Thread, Lock

from core import Player, StandardGameLogic, ClientServer
from ui import MainWindow

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

  RECV_RE = re.compile(r"Recv\((\d*),(\d*),(.*)\)")
  SENT_RE = re.compile(r"Sent\((\d*),(\d*),(.*)\)")

  HIT_RE = re.compile(r"Shot\(Hit\((\d),(\d),(\d)\)\)")
  TRIGGER_RE = re.compile(r"Trigger\(\)")

  eventLock = Lock()
    
  def handleEvent(self, fullLine):
    with self.eventLock:
      print fullLine
      sys.stdout.flush()
  
    m = self.RECV_RE.match(fullLine)
    if(m):
      (recvTeam, recvPlayer, line) = m.groups()

      m = self.HIT_RE.match(line)
      if(m):
        (sentTeam, sentPlayer, damage) = m.groups()

        with self.eventLock:
          player = self.gameState.getOrCreatePlayer(recvTeam, recvPlayer)
          self.logic.hit(player, sentTeam, sentPlayer, damage)
          mainWindow.playerUpdated(recvTeam, recvPlayer)

      m = self.TRIGGER_RE.match(line)
      if(m):
        with self.eventLock:
          player = self.gameState.getOrCreatePlayer(recvTeam, recvPlayer)
          if (self.logic.trigger(player)):
            mainWindow.playerUpdated(recvTeam, recvPlayer)
#            self.logic.hit(player, fromTeam, fromPlayer, damage)

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
