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
      event = proto.parseEvent(fullLine)

      if mainWindow: # This should only be None in tests.
        mainWindow.lineReceived(event)

      self.__handleEvent(event, self.gameState, connection)

    #TODO be more discerning 
    return True

  def __handleEvent(self, event, gameState, connection):
    """handle an event, you must be holding self.eventLock before calling this"""
    msgStr = event.msgStr

    h1 = proto.MessageHandler()

    @h1.handles(proto.RECV)
    def recv(recvTeamStr, recvPlayerStr, line):
      recvTeam = int(recvTeamStr)
      recvPlayer = int(recvPlayerStr)
      player = gameState.getOrCreatePlayer(recvTeam, recvPlayer)

      h2 = proto.MessageHandler()

      @h2.handles(proto.HIT)
      def hit(sentTeamStr, sentPlayerStr, damage):
        sentTeam = int(sentTeamStr)
        sentPlayer = int(sentPlayerStr)

        #TODO: add some sanity checks in here. The shooting player shouldn't be dead at this point 
        self.logic.hit(gameState, player, sentTeam, sentPlayer, damage)
        gameState.playerUpdated.emit(recvTeam, recvPlayer)

      @h2.handles(proto.TRIGGER)
      def trigger():
        if (self.logic.trigger(gameState, player)):
          gameState.playerUpdated.emit(recvTeam, recvPlayer)

      @h2.handles(proto.FULL_AMMO)
      def fullAmmo():
        if (self.logic.fullAmmo(gameState, player)):
          gameState.playerUpdated.emit(recvTeam, recvPlayer)

      return h2.handle(line)

    @h1.handles(proto.HELLO)
    def hello():
      clientId = event.id
      existingIds = self.listeningThread.isConnected(clientId)
      if existingIds:
        #TODO maintain the state of this client by sending it an update (taking our send queue into account).
        #For now, simply remove the ghost player from the game.
        self.gameState.deletePlayer(existingIds[0], existingIds[1])
        player = gameState.getOrCreatePlayer(existingIds[0], existingIds[1])
      else:
        player = gameState.createNewPlayer()
      connection.queueMessage(proto.TEAMPLAYER.create(player.teamID, player.playerID))

      self.listeningThread.establishConnection(connection, player, clientId)

      if self.gameState.isGameStarted():
        connection.queueMessage(proto.STARTGAME.create(self.gameState.gameTimeRemaining()))

    @h1.handles(proto.PING)
    def ping():
      connection.queueMessage(proto.PONG.create(event.time, 1))
          
    @h1.handles(proto.PONG)
    def pong(startTime, reply):
      now = connection.timeProvider()
      latency = (startTime - now) / 2 #TODO, do something with this.
      if reply:
        connection.queueMessage(proto.PONG.create(event.time, 0))
    
    return h1.handle(msgStr)

  def onDisconnect(self, connection):
    print "a client disconnected"
    self.listeningThread.lostConnection(connection)


class Server(ClientServerConnection):
  """A connection from a client to the server. There are many instances of this class, 1 for each connection"""
  outOfContactTime = 120

  def __init__(self, sock, msgHandler):
    ClientServerConnection.__init__(self)
    self.msgHandler = msgHandler
    self.lastContact = time.time()

    self.setSocket(sock)
  
  def handleMsg(self, fullLine):
    self.lastContact = self.timeProvider()

    return self.msgHandler.handleMsg(fullLine, self)

  def onDisconnect(self):
    #not much we can do until they reconnect apart from note the disconnection
    self.msgHandler.onDisconnect(self)
    self.lastContact = -1

  def setSocket(self, sock):
    super(Server, self).setSocket(sock)
    self.startLatencyCheck()

  def isOutOfContact(self):
    return self.lastContact < time.time() - self.outOfContactTime


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
    self.connectedClients = {}

    self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #self.serversocket.bind((socket.gethostname(), ClientServer.PORT))
    self.serversocket.bind((ClientServer.SERVER, ClientServer.PORT))
    self.serversocket.settimeout(1)
    self.serversocket.listen(5)
    self.shouldStop = False

  def run(self):
    #Launch an OOC Check Thread too
    self.oocUpdater = self.OOCUpdater(self)
    self.oocUpdater.start()

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

  def establishConnection(self, server, player, clientId):
    """ Register that a connection has associated itself with a player"""
    self.unestablishedConnections.remove(server)
    self.connections[(player.teamID, player.playerID)] = server
    self.connectedClients[clientId] = (player.teamID, player.playerID)

  def lostConnection(self, server):
    """ Register that a connection has been lost"""
    #remove from here just in case
    try:
      self.unestablishedConnections.remove(server)
    except KeyError:
      pass
    #look the connection up, it isn't worth storing the reverse mapping as this shouldn't happen very often, I hope!
    for key in self.connections:
      if self.connections[key] == server:
        del self.connections[key]
        break

  def isConnected(self, clientId):
    """Check is a client is alredy connected. If so, return the (team, player) tuple otherwise return None"""
    return self.connectedClients.get(clientId)

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

    #Forget about the client Id too. Don't remember that we deleted it, we rely on the client not reconnecting
    for key in self.connectedClients:
      if self.connectedClients[key] == (teamID, playerID):
        del self.connectedClients[key]
        break

  def lookupPlayerAndTeam(self, server):
    for key in self.connections:
      if self.connections[key] == server:
        return key

  def stop(self):
    self.shouldStop = True
    self.serversocket.close()
    self.oocUpdater.stop()

  class OOCUpdater(Thread):
    def __init__(self, listeningThread):
      Thread.__init__(self)
      self.listeningThread = listeningThread
      self.connections = listeningThread.connections
      self.shouldStop = False
      self._triggeredOOCWarning = {}
    
    def stop(self):
      self.shouldStop = True

    def run(self):
      while not self.shouldStop:
        time.sleep(3)

        for server in self.connections:
          if server not in self._triggeredOOCWarning:
            self._triggeredOOCWarning[server] = False

          if (not self._triggeredOOCWarning[server]) and server.isOutOfContact():
            self._triggeredOOCWarning[server] = True
            (teamID, playerID) = self.listeningThread.lookupPlayerAndTeam(server)
            self.gameState.playerOutOfContactUpdated.emit(teamID, playerID, True)

          if self._triggeredOOCWarning[server] and (not server.isOutOfContact()):
            (teamID, playerID) = self.listeningThread.lookupPlayerAndTeam(server)
            self._triggeredOOCWarning[server] = False
            self.gameState.playerOutOfContactUpdated.emit(teamID, playerID, False)


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

  def getOrCreatePlayer(self, sentTeam, sentPlayer):
    if not (sentTeam, sentPlayer) in self.players:
      self.players[(sentTeam, sentPlayer)] = Player(sentTeam, sentPlayer)
      if sentTeam > self.teamCount:
        self.teamCount = sentTeam
        self.teamCountChanged.emit(self.teamCount)
      if sentPlayer > self.largestTeam:
        self.largestTeam = sentPlayer
        self.largestTeamChanged.emit(self.largestTeam)

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
      self.teamCountChanged.emit(self.teamCount)

    if dstPlayerID > self.largestTeam:
      self.largestTeam = dstPlayerID
      self.largestTeamChanged.emit(self.largestTeam)

    if srcTeamID == self.teamCount:
      #check if this was the only player in this team
      self._recalculateTeamCount()

    if srcPlayerID == self.largestTeam:
      #check if this was the only player in this team
      self._recalculateLargestTeam()

    self.listeningThread.movePlayer(srcTeamID, srcPlayerID, dstTeamID, dstPlayerID)
    self.playerMoved.emit(srcTeamID, srcPlayerID, dstTeamID, dstPlayerID)

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
    self.playerDeleted.emit(teamID, playerID)

  def _recalculateTeamCount(self):
    """ Recalculate the team count. return True if it has changed 
        Note that this won't detect if the teamCount is too low so only call this when players have been removed
    """
    for teamID in range(self.teamCount, 0, -1):
      for playerID in range(self.largestTeam, 0, -1):
        if (teamID, playerID) in self.players:
          #still need this team
          if self.teamCount != teamID:
            self.teamCount = teamID
            self.teamCountChanged.emit(self.teamCount)
            
          return

  def _recalculateLargestTeam(self):
    """ Recalculate the largest team. return True if it has changed 
        Note that this won't detect if the largestTeam is too low so only call this when players have been removed
    """
    for playerID in range(self.largestTeam, 0, -1):
      for teamID in range(self.teamCount, 0, -1):
        if (teamID, playerID) in self.players:
          #one team still has this many players
          if self.largestTeam != playerID:
            self.largestTeam = playerID
            self.largestTeamChanged.emit(self.largestTeam)

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
  playerDeleted = Signal(int, int)
  playerMoved = Signal(int, int, int, int)
  largestTeamChanged = Signal(int)
  teamCountChanged = Signal(int)
  playerOutOfContactUpdated = Signal(int, int, bool)

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
