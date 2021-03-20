from __future__ import print_function

import socket
import sys
import time
import json

from player import Player
from core import ClientServer
from connection import ClientServerConnection
import proto
from parameters import Parameters


class ClientConnection(ClientServerConnection):
    def __init__(self, main, game_logic, *args, **kwargs):
        ClientServerConnection.__init__(self, *args, **kwargs)
        self.main = main
        self.game_logic = game_logic
        self.retryCount = 0

        self._openConnection()

    def handleMsg(self, fullLine):
        event = proto.parseEvent(fullLine)
        msg_str = event.msgStr

        h = proto.MessageHandler()

        @h.handles(proto.PLAYER_SNAPSHOT)
        def playerSnapshot(jsonStr):  # pylint: disable=W0612
            self.game_logic.setPlayerSnapshot(time.time(), json.loads(jsonStr, cls=Player.Decoder))

        @h.handles(proto.PARAMETERS_SNAPSHOT)
        def parametersSnapshot(jsonStr):  # pylint: disable=W0612
            self.game_logic.setParametersSnapshot(time.time(), Parameters.fromSimpleTypes(json.loads(jsonStr)))

        @h.handles(proto.STARTGAME)
        def startGame(duration):  # pylint: disable=W0612
            # Note that we assume latency is zero here however the server will be the ultimate arbiter of when a game ends
            # even if the client thinks there is extra time, it will not be able to change the server gamestate
            self.game_logic.startGame(time.time(), int(duration))

        @h.handles(proto.STOPGAME)
        def stopGame():  # pylint: disable=W0612
            self.game_logic.stopGame(time.time())

        @h.handles(proto.DELETED)
        def deleted():  # pylint: disable=W0612
            # just treat this as the game stopping for us.
            self.game_logic.stopGame(time.time())
            # then shutdown as the server won't want us back.
            self.main.shutdown()

        @h.handles(proto.RESETGAME)
        def resetGame():  # pylint: disable=W0612
            self.game_logic.resetGame(time.time())

        @h.handles(proto.PING)
        def ping():  # pylint: disable=W0612
            self.queueMessage(proto.PONG.create(event.time, 0))

        @h.handles(proto.PONG)
        def pong(_startTime, reply):  # pylint: disable=W0612
            if int(reply):
                self.queueMessage(proto.PONG.create(event.time, 0))

        @h.handles(proto.START_INITIALISING)
        def startInitialising():  # pylint: disable=W0612
            self.game_logic.gameState.startInitialisation()

        return h.handle(msg_str)

    def _openConnection(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Connecting to " + ClientServer.SERVER + ":" + str(ClientServer.PORT))
            self.sock.connect((ClientServer.SERVER, ClientServer.PORT))

            self.setSocket(self.sock)
        except socket.error:
            self.onDisconnect()

    def onDisconnect(self):
        self.retryCount = self.retryCount + 1

        # retry with an exponential backoff, from 2 seconds to 32s
        # 2, 4, 8, 16, 32 = 62 + 60 * 32 = 33:02
        if self.retryCount >= 65:
            super.onDisconnect()
            return

        if self.retryCount > 6:
            wait_time = 64 + 32 * (self.retryCount - 6)
        else:
            wait_time = 2 * 2 ** (self.retryCount - 1)
        print("Disconnected from server, waiting " + str(wait_time) + " seconds to try again")
        sys.stdout.flush()
        time.sleep(wait_time)

        self._openConnection()
