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

    # so we don't try to process messages from 2 clients at once.
    eventLock = Lock()

    def handleMsg(self, full_line, connection):
        with self.eventLock:
            event = proto.parseEvent(full_line)

            # TODO: generic commsListener.
            # if mainWindow: # This should only be None in tests.
            #   mainWindow.lineReceived(event)

            self.__handleEvent(event, connection)

        # TODO be more discerning
        return event.time

    def __handleEvent(self, event, connection):
        """handle an event, you must be holding self.eventLock before calling this"""
        h1 = proto.MessageHandler()

        @h1.handles(proto.RECV)
        def recv(recvTeamStr, recvPlayerStr, line):  # pylint: disable=W0612
            recv_team = int(recvTeamStr)
            recv_player = int(recvPlayerStr)

            h2 = proto.MessageHandler()

            @h2.handles(proto.HIT)
            def hit(sentTeamStr, sentPlayerStr, damageStr):  # pylint: disable=W0612
                sent_team = int(sentTeamStr)
                sent_player = int(sentPlayerStr)
                damage = int(damageStr)

                server_time = connection.clientTimeToServer(event.time)

                self.gameLogic.hit(server_time, recv_team, recv_player, sent_team, sent_player, damage)

            @h2.handles(proto.INIT_HIT)
            def initHit():  # pylint: disable=W0612
                # This is a shot from a gun which is initialising.
                # TODO: allow the UI to pick the team
                player = self.gameLogic.gameState.createNewPlayer()

                self.finishInitialisation(player, self.listeningThread.initialisingConnection)

            @h2.handles(proto.TRIGGER)
            def trigger():  # pylint: disable=W0612
                server_time = connection.clientTimeToServer(event.time)

                self.gameLogic.trigger(server_time, recv_team, recv_player)

            @h2.handles(proto.TRIGGER_RELEASE)
            def triggerRelease():  # pylint: disable=W0612
                server_time = connection.clientTimeToServer(event.time)

                self.gameLogic.triggerRelease(server_time, recv_team, recv_player)

            @h2.handles(proto.FULL_AMMO)
            def fullAmmo():  # pylint: disable=W0612
                pass
                # server_time = connection.clientTimeToServer(event.time)

                # TODO
                # self.gameLogic.fullAmmo(serverTime, recvTeam, recvPlayer)

            return h2.handle(line)

        @h1.handles(proto.HELLO)
        def hello():  # pylint: disable=W0612
            client_id = event.id
            existing_ids = self.listeningThread.isConnected(client_id)
            self.listeningThread.recievedHello(connection, client_id)
            if existing_ids:
                player = self.gameLogic.gameState.getOrCreatePlayer(existing_ids[0], existing_ids[1])
                self.finishInitialisation(player, connection)

        @h1.handles(proto.PING)
        def ping():  # pylint: disable=W0612
            connection.queueMessage(proto.PONG.create(event.time, 1))

        @h1.handles(proto.PONG)
        def pong(startTime, reply):  # pylint: disable=W0612
            now = time.time()
            latency = (now - int(startTime)) / 2
            connection.setLatency(latency)
            connection.setClientClockDrift(event.time - (now - latency))

            if int(reply):
                connection.queueMessage(proto.PONG.create(event.time, 0))

        return h1.handle(event.msgStr)

    def finishInitialisation(self, player, connection):
        connection.queueMessage(proto.PLAYER_SNAPSHOT.create(json.dumps(player, cls=Player.Encoder)))
        parameters_dict = self.gameLogic.gameState.withCurrGameState(lambda s: s.parameters.toSimpleTypes())
        connection.queueMessage(proto.PARAMETERS_SNAPSHOT.create(json.dumps(parameters_dict)))

        self.listeningThread.establishConnection(connection, player)

        if self.gameLogic.gameState.isGameStarted():
            connection.queueMessage(proto.STARTGAME.create(self.gameLogic.gameState.gameTimeRemaining()))
