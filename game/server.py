#!/usr/bin/python

import argparse
import socket
import sys
import time
import traceback
from threading import Thread, Lock, Timer

from core import Player, StandardGameLogic, ClientServer, GameState
from ui import MainWindow
from connection import ClientServerConnection
import proto

from PySide.QtGui import QApplication

class Server(ClientServerConnection):
  def __init__(self, listeningThread, gameState, sock):
    ClientServerConnection.__init__(self)
    self.listeningThread = listeningThread
    self.logic = StandardGameLogic()
    self.gameState = gameState

    self.setSocket(sock)
  
  #so we don't try to process messages from 2 clients at once.
  eventLock = Lock()
    
  def handleMsg(self, fullLine):
    with self.eventLock:
      print fullLine
      mainWindow.lineReceived(fullLine)
      sys.stdout.flush()
  
    try:
      (recvTeam, recvPlayer, line) = proto.RECV.parse(fullLine)

      try:
        (sentTeam, sentPlayer, damage) = proto.HIT.parse(line)

        with self.eventLock:
          player = self.gameState.getOrCreatePlayer(recvTeam, recvPlayer)
          self.logic.hit(self.gameState, player, sentTeam, sentPlayer, damage)
          mainWindow.playerUpdated(recvTeam, recvPlayer)
      except proto.MessageParseException:
        pass

      try:
        proto.TRIGGER.parse(line)

        with self.eventLock:
          player = self.gameState.getOrCreatePlayer(recvTeam, recvPlayer)
          if (self.logic.trigger(self.gameState, player)):
            mainWindow.playerUpdated(recvTeam, recvPlayer)
      except proto.MessageParseException:
        pass

    except proto.MessageParseException:
      pass

    try:
      (teamID, playerID) = proto.HELLO.parse(fullLine)

      with self.eventLock:
        if int(teamID) == -1:
          player = self.gameState.createNewPlayer()
          self.queueMessage("TeamPlayer(%s,%s)\n" % (player.teamID, player.playerID))
        else:
          player = self.gameState.getOrCreatePlayer(teamID, playerID)
          self.queueMessage("Ack()\n")
        #TODO: we need to preserve the sendQueue when we do this
        self.listeningThread.moveConnection(self, player)
          
        #TODO if the game has started, also tell the client this.
        if self.gameState.isGameStarted():
          self.queueMessage("StartGame(%d)\n" % (self.gameState.gameTimeRemaining()))
    except proto.MessageParseException:
      pass

    return "Ack()\n"

  def onDisconnect(self):
    #not much we can do until they reconnect
    pass


class ListeningThread(Thread):

  def __init__(self, gameState):
    super(ListeningThread, self).__init__(group=None)
    self.name = "Server Listening Thread"
    self.gameState = gameState
    gameState.setListeningThread(self)

    self.connections = {}
    self.unestablishedConnections = set()

    self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #self.serversocket.bind((socket.gethostname(), ClientServer.PORT))
    self.serversocket.bind((ClientServer.SERVER, ClientServer.PORT))
    self.serversocket.settimeout(1)
    self.serversocket.listen(5)
    self.shouldStop = False

  def run(self):
    #start serving
    while True:
      if self.shouldStop:
        return

      try:
        (clientsocket, address) = self.serversocket.accept();
        self.unestablishedConnections.add(Server(self, gameState, clientsocket))
      except KeyboardInterrupt:
        break
      except socket.timeout:
        pass

  def moveConnection(self, server, player):
    self.unestablishedConnections.remove(server)
    self.connections[(player.teamID, player.playerID)] = server
    
  def queueMessageToAll(self, msg):
    for key in self.connections:
      self.connections[key].queueMessage(msg)

  def queueMessage(self, teamID, playerID, msg):
    self.connections[(teamID, playerID)].queueMessage(msg)

  def movePlayer(self, srcTeamID, srcPlayerID, dstTeamID, dstPlayerID):
    self.connections[(dstTeamID, dstPlayerID)] = self.connections[(srcTeamID, srcPlayerID)]
    del self.connections[(srcTeamID, srcPlayerID)]
    self.queueMessage(dstTeamID, dstPlayerID, "TeamPlayer(%s,%s)\n" % (dstTeamID, dstPlayerID))

  def stop(self):
    self.shouldStop = True
    self.serversocket.close()

GAME_TIME=1200 #20 mins
#GAME_TIME=12

class ServerGameState(GameState):
  def __init__(self):
    GameState.__init__(self)
    self.players = {}
    self.teamCount = 0
    self.largestTeam = 0
    self.stopGameTimer = None
    self.targetTeamCount = 2
  
  def setListeningThread(self, lt):
    self.listeningThread = lt

  def getOrCreatePlayer(self, sentTeamStr, sentPlayerStr):
    sentTeam = int(sentTeamStr)
    sentPlayer = int(sentPlayerStr)

    if not (sentTeam, sentPlayer) in self.players:
      self.players[(sentTeam, sentPlayer)] = Player(sentTeam, sentPlayer)
      if sentTeam > self.teamCount:
        self.teamCount = sentTeam
      if sentPlayer > self.largestTeam:
        self.largestTeam = sentPlayer

      mainWindow.playerAdded(sentTeam, sentPlayer);
    return self.players[(sentTeam, sentPlayer)]

  def createNewPlayer(self):
    for playerID in range(1, 32):
      for teamID in range(1, self.targetTeamCount + 1):
        if (teamID, playerID) not in self.players:
          return self.getOrCreatePlayer(teamID, playerID)
    #TODO handle this
    raise RuntimeError("too many players")

  def movePlayer(self, srcTeamID, srcPlayerID, dstTeamID, dstPlayerID):
    print "Moving %d:%d =>%d:%d" % (srcTeamID, srcPlayerID, dstTeamID, dstPlayerID)
    if (dstTeamID, dstPlayerID) in self.players:
      raise RuntimeError("Tried to move a player to a non-empty spot")
    if (srcTeamID, srcPlayerID) not in self.players:
      return

    player = self.players[(srcTeamID, srcPlayerID)]
    self.players[(dstTeamID, dstPlayerID)] = player
    player.teamID = dstTeamID
    player.playerID = dstPlayerID
    #TODO: should we reset their stats.
    del self.players[(srcTeamID, srcPlayerID)]

    if dstTeamID > self.teamCount:
      self.teamCount = dstTeamID

    if dstPlayerID > self.largestTeam:
      self.largestTeam = dstPlayerID

    self.listeningThread.movePlayer(srcTeamID, srcPlayerID, dstTeamID, dstPlayerID)
    #TODO: notify people of the change

  def startGame(self):
    self.gameStartTime = time.time()
    self.gameEndTime = time.time() + GAME_TIME
    def timerStop():
      if self.gameStartTime + GAME_TIME > time.time():
        #the game must have been stopped and restarted as we aren't ready to stop yet. Why were we not cancelled though?
        raise RuntimeError("timer seemingly triggered early")
      self.stopGame()
    self.stopGameTimer = Timer(GAME_TIME, timerStop)
    self.stopGameTimer.start()
    self.listeningThread.queueMessageToAll("StartGame(%d)\n" % (GAME_TIME))

  def stopGame(self):
    self.gameEndTime = None
    self.gameStartTime = None
    self.listeningThread.queueMessageToAll("StopGame()\n")
    if self.stopGameTimer:
      self.stopGameTimer.cancel()
    self.stopGameTimer = None

  def setTargetTeamCount(self, value):
    self.targetTeamCount = value

  def terminate(self):
    self.stopGame()

parser = argparse.ArgumentParser(description='BraidsTag server.')
args = parser.parse_args()

gameState = ServerGameState()

main = ListeningThread(gameState)
main.start()

# Create Qt application
app = QApplication(sys.argv)
mainWindow = MainWindow(gameState)
mainWindow.show()

# Enter Qt main loop
retval = app.exec_()

for i in gameState.players.values():
  print i

main.stop()
gameState.terminate()

#print >> sys.stderr, "\n*** STACKTRACE - START ***\n"
#code = []
#for threadId, stack in sys._current_frames().items():
#    code.append("\n# ThreadID: %s" % threadId)
#    for filename, lineno, name, line in traceback.extract_stack(stack):
#        code.append('File: "%s", line %d, in %s' % (filename,
#                                                    lineno, name))
#        if line:
#            code.append("  %s" % (line.strip()))
#
#for line in code:
#    print >> sys.stderr, line
#print >> sys.stderr, "\n*** STACKTRACE - END ***\n"
#

sys.exit(retval)
