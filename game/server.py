#!/usr/bin/python

import argparse
import re
import socket
import sys
from threading import Thread, Lock

from core import Player, StandardGameLogic, ClientServer

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtDeclarative import QDeclarativeView
 

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

class GameState(QObject):
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

      mainWindow.listModel.layoutChanged.emit(); #TODO: this is a bit of a blunt instrument.
      #mainWindow.listModel.dataChanged.emit(mainWindow.listModel.index(sentTeam, sentPlayer, QModelIndex()), mainWindow.listModel.index(sentTeam, sentPlayer, QModelIndex()))
    return self.players[(sentTeam, sentPlayer)]

class GameStateModel(QAbstractTableModel):
  """
  A Model which represents the players' gameState. The team is the column and the player is the row.
  """
  def rowCount(self, index):
    return ClientThread.gameState.largestTeam

  def columnCount(self, index):
    return ClientThread.gameState.teamCount

  def data(self, index, role = Qt.DisplayRole):
    if not index.isValid():
      return None

    if role == Qt.DisplayRole:
      indexTuple = (index.column() + 1, index.row() + 1)
      if indexTuple not in ClientThread.gameState.players:
        return None
      return str(ClientThread.gameState.players[indexTuple])

    return None

  def playerUpdated(teamID, playerID):
    self.dataChanged.emit(self.index(recvPlayer, recvTeam, QModelIndex()), self.index(recvPlayer, recvTeam, QModelIndex()))


class LinearModel(QAbstractListModel):
  def __init__(self, source):
    super(LinearModel, self).__init__()
    self.source = source
    QObject.connect(self.source, SIGNAL('dataChanged()'), self.dataChangedDelegate)

  def rowCount(self, index):
    return self.source.rowCount(index) * self.source.columnCount(index)

  def columnCount(self, index):
    return 1

  def data(self, index, role = Qt.DisplayRole):
    return self.source.data(self.source.index(index.row() % self.source.columnCount(index.parent()), index.row() // self.source.columnCount(index.parent()), index.parent()), role)

  def dataChangedDelegate(self, startIndex, endIndex):
    self.dataChanged.emit(self.index(0, startIndex.row() * startIndex.column(), QModelIndex()), self.index(0, endIndex.row() * endIndex.column(), QModelIndex()))

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

    self.handleEvent(msg)

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
          mainWindow.listModel.playerUpdated(recvTeam, recvPlayer)

      m = self.TRIGGER_RE.match(line)
      if(m):
        with self.eventLock:
          player = self.gameState.getOrCreatePlayer(recvTeam, recvPlayer)
          if (self.logic.trigger(player)):
            mainWindow.listModel.playerUpdated(recvTeam, recvPlayer)
#            self.logic.hit(player, fromTeam, fromPlayer, damage)

def stringToPlayerID(inp):
  out = int(inp)
  if out < 1 or out > 32:
    raise argparse.ArgumentTypeError("playerId must be between 1 and 32.")
  return out;

class MainWindow(QDialog):
  def __init__(self, parent=None):
    super(MainWindow, self).__init__(parent)
    self.setWindowTitle("BraidsTag Server")

    self.layout = QVBoxLayout()
    self.listModel = LinearModel(GameStateModel())
    self.listView = QListView()
    self.listView.setModel(self.listModel)
    self.layout.addWidget(self.listView)

    self.setLayout(self.layout)

main = ListeningThread()
main.start()

# Create Qt application
app = QApplication(sys.argv)
mainWindow = MainWindow()
mainWindow.show()

# Enter Qt main loop
retval = app.exec_()
for i in ClientThread.gameState.players.values():
  print i

sys.exit(retval)
