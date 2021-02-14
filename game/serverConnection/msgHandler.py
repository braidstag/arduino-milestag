#!/usr/bin/python

from __future__ import print_function

import time
from threading import Lock
import json

import proto
from player import Player

class ServerMsgHandler():
  """A class to handle messages from clients to the server. There should only be one instance of this class""" 
  def __init__(self, listeningThread, gameLogic):
    self.listeningThread = listeningThread
    self.gameLogic = gameLogic

  #so we don't try to process messages from 2 clients at once.
  eventLock = Lock()

  def handleMsg(self, fullLine, connection):
    with self.eventLock:
      event = proto.parseEvent(fullLine)

      #TODO: generic commsListener.
      # if mainWindow: # This should only be None in tests.
      #   mainWindow.lineReceived(event)

      self.__handleEvent(event, connection)

    #TODO be more discerning
    return event.time

  def __handleEvent(self, event, connection):
    """handle an event, you must be holding self.eventLock before calling this"""
    h1 = proto.MessageHandler()

    @h1.handles(proto.RECV)
    def recv(recvTeamStr, recvPlayerStr, line): # pylint: disable=W0612
      recvTeam = int(recvTeamStr)
      recvPlayer = int(recvPlayerStr)

      h2 = proto.MessageHandler()

      @h2.handles(proto.HIT)
      def hit(sentTeamStr, sentPlayerStr, damageStr): # pylint: disable=W0612
        sentTeam = int(sentTeamStr)
        sentPlayer = int(sentPlayerStr)
        damage = int(damageStr)

        serverTime = connection.clientTimeToServer(event.time)

        self.gameLogic.hit(serverTime, recvTeam, recvPlayer, sentTeam, sentPlayer, damage)

      @h2.handles(proto.INIT_HIT)
      def initHit(): # pylint: disable=W0612
        # This is a shot from a gun which is initialising.
        # TODO: allow the UI to pick the team
        player = self.gameLogic.gameState.createNewPlayer()

        self.finishInitialisation(player, connection, self.listeningThread.initialisingConnection.clientId)

      @h2.handles(proto.TRIGGER)
      def trigger(): # pylint: disable=W0612
        serverTime = connection.clientTimeToServer(event.time)

        self.gameLogic.trigger(serverTime, recvTeam, recvPlayer)

      @h2.handles(proto.TRIGGER_RELEASE)
      def triggerRelease(): # pylint: disable=W0612
        serverTime = connection.clientTimeToServer(event.time)

        self.gameLogic.triggerRelease(serverTime, recvTeam, recvPlayer)

      @h2.handles(proto.FULL_AMMO)
      def fullAmmo(): # pylint: disable=W0612
        serverTime = connection.clientTimeToServer(event.time)

        #TODO
        #self.gameLogic.fullAmmo(serverTime, recvTeam, recvPlayer)

      return h2.handle(line)

    @h1.handles(proto.HELLO)
    def hello(): # pylint: disable=W0612
      clientId = event.id
      existingIds = self.listeningThread.isConnected(clientId)
      if existingIds:
        player = self.gameLogic.gameState.getOrCreatePlayer(existingIds[0], existingIds[1])
        self.finishInitialisation(player, connection, clientId)
      else:
        self.listeningThread.recievedHello(connection, clientId)

    @h1.handles(proto.PING)
    def ping(): # pylint: disable=W0612
      connection.queueMessage(proto.PONG.create(event.time, 1))

    @h1.handles(proto.PONG)
    def pong(startTime, reply): # pylint: disable=W0612
      now = time.time()
      latency = (now - int(startTime)) / 2
      connection.setLatency(latency)
      connection.setClientClockDrift(event.time - (now - latency))

      if int(reply):
        connection.queueMessage(proto.PONG.create(event.time, 0))

    return h1.handle(event.msgStr)

  def finishInitialisation(self, player, connection, clientId):
    connection.queueMessage(proto.PLAYER_SNAPSHOT.create(json.dumps(player, cls=Player.Encoder)))
    parametersDict = self.gameLogic.gameState.withCurrGameState(lambda s: s.parameters.toSimpleTypes())
    connection.queueMessage(proto.PARAMETERS_SNAPSHOT.create(json.dumps(parametersDict)))

    self.listeningThread.establishConnection(connection, player, clientId)

    if self.gameLogic.gameState.isGameStarted():
      connection.queueMessage(proto.STARTGAME.create(self.gameLogic.gameState.gameTimeRemaining()))
