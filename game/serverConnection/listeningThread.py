#!/usr/bin/python

from __future__ import print_function

import socket
import time
from threading import Thread

from core import ClientServer
import proto
from serverConnection import ServerConnection
from msgHandler import ServerMsgHandler

class ListeningThread(Thread):
  """A thread which listens for new connections from a client.
     Spawns a Server instance to handle the ongoing communication and stores them all to enable sending broadcast messages
  """
  def __init__(self, gameLogic):
    super(ListeningThread, self).__init__(group=None)
    self.name = "Server Listening Thread"
    self.gameLogic = gameLogic
    #gameState.setListeningThread(self)

    self.msgHandler = ServerMsgHandler(self, gameLogic)

    self.connections = {}
    self.unestablishedConnections = set()
    self.connectedClients = {}

    print ("Starting server on ", ClientServer.SERVER, ":", ClientServer.PORT)
    self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        (clientsocket, dummy_address) = self.serversocket.accept()
        #this function is added to the class dynamically so pylint doesn't think it is there.
        clientsocket.setblocking(1) #pylint:disable=no-member
        self.unestablishedConnections.add(ServerConnection(clientsocket, self, self.msgHandler))
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

  def considerMovingConfidencePoint(self, changedTime):
    """Check if the message we just recieved at the given time moves the confidence point
     and, if so. Tell the GameState about it"""
    if (len(self.connections) == 0):
      return
    earliestLastContact = min([x.lastContact for x in self.connections.values()])
    if (earliestLastContact == changedTime):
      #This has bumped up the confidence point
      self.gameLogic.gameState.adjustConfidencePoint(earliestLastContact)

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

        for key, server in self.connections.items():
          if key not in self._triggeredOOCWarning:
            self._triggeredOOCWarning[key] = False

          if server.isOutOfContact():
            self._triggeredOOCWarning[key] = True
            (teamID, playerID) = key
            #TODO
            #self.listeningThread.gameState.playerOutOfContactUpdated.emit(teamID, playerID, True)

          if self._triggeredOOCWarning[key] and (not server.isOutOfContact()):
            (teamID, playerID) = key
            self._triggeredOOCWarning[key] = False
            #TODO
            #self.listeningThread.gameState.playerOutOfContactUpdated.emit(teamID, playerID, False)