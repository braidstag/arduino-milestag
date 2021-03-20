#!/usr/bin/python

from __future__ import print_function

import socket
import time
from threading import Thread
import json

from core import ClientServer
import proto
from serverConnection import ServerConnection
from msgHandler import ServerMsgHandler
from player import Player


class ListeningThread(Thread):
    """A thread which listens for new connections from a client.
       Spawns a Server instance to handle the ongoing communication and stores them all to enable sending broadcast messages
    """
    def __init__(self, game_logic):
        super(ListeningThread, self).__init__(group=None)
        self.name = "Server Listening Thread"
        self.gameLogic = game_logic

        self.msgHandler = ServerMsgHandler(self, game_logic)

        game_logic.gameState.addListener(playerMoved=self.movePlayer)

        self.connections = {}
        self.disconnectedConnections = set()  # We have a tcp connection but haven't received an application payload
        self.uninitialisedConnections = set()  # We have received an application payload but not in the game yet.
        self.initialisingConnection = None
        self.connectedClients = {}

        print ("Starting game server on", ClientServer.SERVER, ":", ClientServer.PORT)
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind((ClientServer.SERVER, ClientServer.PORT))
        self.serversocket.settimeout(1)
        self.serversocket.listen(5)
        self.shouldStop = False

    def run(self):
        # Launch an OOC Check Thread too
        self.oocUpdater = self.OOCUpdater(self)
        self.oocUpdater.start()

        # start serving
        while True:
            if self.shouldStop:
                return

            try:
                (clientsocket, dummy_address) = self.serversocket.accept()
                # this function is added to the class dynamically so pylint doesn't think it is there.
                clientsocket.setblocking(1)  # pylint:disable=no-member
                self.disconnectedConnections.add(ServerConnection(clientsocket, self, self.msgHandler))
            except KeyboardInterrupt:
                break
            except socket.timeout:
                pass

    def recievedHello(self, server, client_id):
        """ Register that we have received the first application message from a client """
        try:
            self.disconnectedConnections.remove(server)
        except KeyError:
            pass

        self.uninitialisedConnections.add(server)
        server.clientId = client_id
        self.gameLogic.gameState._notifyConnectionsChangedListeners()

    def startInitialising(self, server):
        """ Register that a particular client has been selected as initialising """
        try:
            self.uninitialisedConnections.remove(server)
        except KeyError:
            pass
        if self.initialisingConnection:
            print("started initialisation when we already had an uninitialised client")

        self.initialisingConnection = server
        server.queueMessage(proto.START_INITIALISING.create())
        self.gameLogic.gameState._notifyPlayerInitialisingListeners()

    def establishConnection(self, server, player):
        """ Register that a connection has associated itself with a player"""
        try:
            self.uninitialisedConnections.remove(server)
        except KeyError:
            pass
        try:
            self.disconnectedConnections.remove(server)
        except KeyError:
            pass
        if self.initialisingConnection == server:
            self.initialisingConnection = None

        self.connections[(player.team_id, player.player_id)] = server
        self.connectedClients[server.clientId] = (player.team_id, player.player_id)
        self.gameLogic.gameState._notifyPlayerInitialisedListeners()

    def lostConnection(self, server):
        """ Register that a connection has been lost"""
        # remove from here just in case
        try:
            self.uninitialisedConnections.remove(server)
        except KeyError:
            pass
        try:
            self.disconnectedConnections.remove(server)
        except KeyError:
            pass
        if self.initialisingConnection == server:
            self.initialisingConnection = None

        # look the connection up, it isn't worth storing the reverse mapping as this shouldn't happen very often, I hope!
        for key in self.connections:
            if self.connections[key] == server:
                del self.connections[key]
                break

    def isConnected(self, client_id):
        """Check is a client is already connected. If so, return the (team, player) tuple otherwise return None"""
        return self.connectedClients.get(client_id)

    def queueMessageToAll(self, msg):
        """ send a message to all clients. Note that this doesn't include unestablished connections."""
        for key in self.connections:
            self.connections[key].queueMessage(msg)

    def queueMessage(self, team_id, player_id, msg):
        if (team_id, player_id) in self.connections:
            self.connections[(team_id, player_id)].queueMessage(msg)

    def movePlayer(self, src_team_id, src_player_id, player):
        if (src_team_id, src_player_id) in self.connections:
            self.connections[(player.team_id, player.player_id)] = self.connections[(src_team_id, src_player_id)]
            del self.connections[(src_team_id, src_player_id)]
            self.queueMessage(player.team_id, player.player_id, proto.PLAYER_SNAPSHOT.create(json.dumps(player, cls=Player.Encoder)))
            # TODO: should effects move as well?

    def deletePlayer(self, team_id, player_id):
        self.queueMessage(team_id, player_id, proto.DELETED.create())
        if (team_id, player_id) in self.connections:
            del self.connections[(team_id, player_id)]

        # Forget about the client Id too. Don't remember that we deleted it, we rely on the client not reconnecting
        for key in self.connectedClients:
            if self.connectedClients[key] == (team_id, player_id):
                del self.connectedClients[key]
                break

    def considerMovingConfidencePoint(self, changed_time):
        """Check if the message we just recieved at the given time moves the confidence point
         and, if so. Tell the GameState about it"""
        if len(self.connections) == 0:
            return
        earliest_last_contact = min([x.lastContact for x in self.connections.values()])
        if earliest_last_contact == changed_time:
            # This has bumped up the confidence point
            self.gameLogic.gameState.adjustConfidencePoint(earliest_last_contact)

    def stop(self):
        self.shouldStop = True
        self.serversocket.close()
        self.oocUpdater.stop()

    class OOCUpdater(Thread):
        def __init__(self, listening_thread):
            Thread.__init__(self)
            self.name = "OOCUpdater"
            self.listeningThread = listening_thread
            self.connections = listening_thread.connections
            self.shouldStop = False
            self._triggeredOOCWarning = {}

        def stop(self):
            self.shouldStop = True

        def run(self):
            latency_check_interval = 30
            last_triggered_latency_check = 0
            while not self.shouldStop:
                time.sleep(3)

                # ping to test latency.
                if time.time() > last_triggered_latency_check + latency_check_interval:
                    last_triggered_latency_check = time.time()
                    for key, server in self.connections.items():
                        server.startLatencyCheck()

                # Check if we have gone out of contact
                for key, server in self.connections.items():
                    if key not in self._triggeredOOCWarning:
                        self._triggeredOOCWarning[key] = False

                    if server.isOutOfContact():
                        self._triggeredOOCWarning[key] = True
                        # (team_id, player_id) = key
                        # TODO
                        # self.listeningThread.gameState.playerOutOfContactUpdated.emit(team_id, player_id, True)

                    if self._triggeredOOCWarning[key] and (not server.isOutOfContact()):
                        # (team_id, player_id) = key
                        self._triggeredOOCWarning[key] = False
                        # TODO
                        # self.listeningThread.gameState.playerOutOfContactUpdated.emit(team_id, player_id, False)
