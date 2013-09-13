#!/usr/bin/python

import argparse
import socket
import sys
import time
import traceback
from threading import Thread, Lock, Timer
from bisect import insort

from core import Player, StandardGameLogic, ClientServer, GameState
from ui import MainWindow
from connection import ClientServerConnection
import proto

from PySide.QtGui import QApplication
from PySide.QtCore import Signal

class ServerMsgHandler():
  """A class to handle messages from clients to the server. There should only be one instance of this class""" 
  def __init__(self, listeningThread, gameState):
    self.listeningThread = listeningThread
    self.logic = StandardGameLogic()
    self.gameState = gameState

  #so we don't try to process messages from 2 clients at once.
  eventLock = Lock()
    
  def handleMsg(self, fullLine, connection):
    with self.eventLock:
      if mainWindow: # This should only be None in tests.
        mainWindow.lineReceived(fullLine)

      event = proto.parseEvent(fullLine)

      self.__handleEvent(event, self.gameState, connection)

    #TODO be more discerning 
    return True

  def __handleEvent(self, event, gameState, connection):
    """handle an event, you must be holding self.eventLock before calling this"""
    msgStr = event.msgStr

    h1 = proto.MessageHandler()

    @h1.handles(proto.RECV)
    def recv(recvTeam, recvPlayer, line):
      h2 = proto.MessageHandler()

      @h2.handles(proto.HIT)
      def hit(sentTeam, sentPlayer, damage):
        #TODO: add some sanity checks in here. The shooting player shouldn't be dead at this point 

        player = gameState.getOrCreatePlayer(recvTeam, recvPlayer)
        self.logic.hit(gameState, player, sentTeam, sentPlayer, damage)
        gameState.playerUpdated.emit(recvTeam, recvPlayer)

        return True

      @h2.handles(proto.TRIGGER)
      def trigger():
        player = gameState.getOrCreatePlayer(recvTeam, recvPlayer)
        if (self.logic.trigger(gameState, player)):
          gameState.playerUpdated.emit(recvTeam, recvPlayer)

        return True

      @h2.handles(proto.FULL_AMMO)
      def fullAmmo():
        player = gameState.getOrCreatePlayer(recvTeam, recvPlayer)
        if (self.logic.fullAmmo(gameState, player)):
          gameState.playerUpdated.emit(recvTeam, recvPlayer)

        return True

      return h2.handle(line)

    @h1.handles(proto.HELLO)
    def hello():
      clientId = event.id
      #if self.listeningThread.isConnected(clientId):
      #  #TODO maintain the state of this client by sending it an update.
      #  #For now, simply remove the ghost player from the game.
      #  self.listeningThread.disconnected(clientId):

      player = gameState.createNewPlayer()
      connection.queueMessage(proto.TEAMPLAYER.create(player.teamID, player.playerID))

      self.listeningThread.establishConnection(connection, player)

      if self.gameState.isGameStarted():
        connection.queueMessage(proto.STARTGAME.create(self.gameState.gameTimeRemaining()))

      return True

    return h1.handle(msgStr)


class Server(ClientServerConnection):
  """A connection from a client to the server. There are many instaces of this class, 1 for each connection"""
  def __init__(self, sock, msgHandler):
    ClientServerConnection.__init__(self)
    self.msgHandler = msgHandler

    self.setSocket(sock)
  
  def handleMsg(self, fullLine):
    return self.msgHandler.handleMsg(fullLine, self)

  def onDisconnect(self):
    #not much we can do until they reconnect
    pass


class ListeningThread(Thread):
  """A thread which listens for new connections from a client. 
     Spawns a Server instance to handle the ongoing communication and stores them all to enable sending broadcast messages
  """

  def __init__(self, gameState):
    super(ListeningThread, self).__init__(group=None)
    self.name = "Server Listening Thread"
    self.gameState = gameState
    gameState.setListeningThread(self)

    self.msgHandler = ServerMsgHandler(self, gameState)

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
        self.unestablishedConnections.add(Server(clientsocket, self.msgHandler))
      except KeyboardInterrupt:
        break
      except socket.timeout:
        pass

  def establishConnection(self, server, player):
    """ Register that a connection has associated itself with a player"""
    #TODO: we need to preserve the sendQueue when we do this
    self.unestablishedConnections.remove(server)
    self.connections[(player.teamID, player.playerID)] = server

  def queueMessageToAll(self, msg):
    for key in self.connections:
      self.connections[key].queueMessage(msg)

  def queueMessage(self, teamID, playerID, msg):
    if (teamID, playerID) in self.connections:
      self.connections[(teamID, playerID)].queueMessage(msg)

  def movePlayer(self, srcTeamID, srcPlayerID, dstTeamID, dstPlayerID):
    #TODO: we need to preserve the sendQueue when we do this
    if (srcTeamID, srcPlayerID) in self.connections:
      self.connections[(dstTeamID, dstPlayerID)] = self.connections[(srcTeamID, srcPlayerID)]
      del self.connections[(srcTeamID, srcPlayerID)]
      self.queueMessage(dstTeamID, dstPlayerID, proto.TEAMPLAYER.create(dstTeamID, dstPlayerID))

  def deletePlayer(self, teamID, playerID):
    self.queueMessage(teamID, playerID, proto.DELETED.create())
    if (teamID, playerID) in self.connections:
      del self.connections[(teamID, playerID)]

  def stop(self):
    self.shouldStop = True
    self.serversocket.close()

#initial game settings, these are told to the clients and can be changed in the UI. 
GAME_TIME=1200 #20 mins
#GAME_TIME=12
TEAM_COUNT=2

class ServerGameState(GameState):
  """A store of all of the gamestate which the server knows about. There is only one instance of this class on the server."""
  def __init__(self):
    GameState.__init__(self)
    self.players = {}
    self.teamCount = 0
    self.largestTeam = 0
    self.stopGameTimer = None
    self.targetTeamCount = TEAM_COUNT
    self.setGameTime(GAME_TIME)
  
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

      self.playerAdded.emit(sentTeam, sentPlayer)
    return self.players[(sentTeam, sentPlayer)]

  def createNewPlayer(self):
    for playerID in range(1, 33):
      for teamID in range(1, self.targetTeamCount + 1):
        if (teamID, playerID) not in self.players:
          return self.getOrCreatePlayer(teamID, playerID)
    #TODO handle this
    raise RuntimeError("too many players")

  def movePlayer(self, srcTeamID, srcPlayerID, dstTeamID, dstPlayerID):
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

    if srcTeamID == self.teamCount:
      #check if this was the only player in this team
      self._recalculateTeamCount()

    if srcPlayerID == self.largestTeam:
      #check if this was the only player in this team
      self._recalculateLargestTeam()

    self.listeningThread.movePlayer(srcTeamID, srcPlayerID, dstTeamID, dstPlayerID)
    #TODO: notify people of the change

  def deletePlayer(self, teamID, playerID):
    if (teamID, playerID) not in self.players:
      return

    del self.players[(teamID, playerID)]

    if teamID == self.teamCount:
      #check if this was the only player in this team
      self._recalculateTeamCount()

    if playerID == self.largestTeam:
      #check if this was the only player in this team
      self._recalculateLargestTeam()

    self.listeningThread.deletePlayer(teamID, playerID)

  def _recalculateTeamCount(self):
    for teamID in range(self.teamCount, 0, -1):
      for playerID in range(self.largestTeam, 0, -1):
        if (teamID, playerID) in self.players:
          #still need this team
          self.teamCount = teamID
          return

  def _recalculateLargestTeam(self):
    for playerID in range(self.largestTeam, 0, -1):
      for teamID in range(self.teamCount, 0, -1):
        if (teamID, playerID) in self.players:
          #one team still has this many players
          self.largestTeam = playerID
          return

  def startGame(self):
    GameState.startGame(self)
    def timerStop():
      if self.gameStartTime + self.gameTime > time.time():
        #the game must have been stopped and restarted as we aren't ready to stop yet. Why were we not cancelled though?
        raise RuntimeError("timer seemingly triggered early")
      self.stopGame()
    self.stopGameTimer = Timer(self.gameTime, timerStop)
    self.stopGameTimer.start()
    self.listeningThread.queueMessageToAll(proto.STARTGAME.create(self.gameTime))

  def stopGame(self):
    GameState.stopGame(self)
    self.listeningThread.queueMessageToAll(proto.STOPGAME.create())
    if self.stopGameTimer:
      self.stopGameTimer.cancel()
    self.stopGameTimer = None

  def resetGame(self):
    #GameState.resetGame(self)
    self.listeningThread.queueMessageToAll(proto.RESETGAME.create())
    for p in gameState.players.values():
      p.reset()
      self.playerUpdated.emit(p.teamID, p.playerID)

  def setTargetTeamCount(self, value):
    self.targetTeamCount = value

  def terminate(self):
    self.stopGame()

  playerAdded = Signal(int, int)
  playerUpdated = Signal(int, int)

#TODO don't have this as a global
mainWindow = None

if __name__ == '__main__':
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
