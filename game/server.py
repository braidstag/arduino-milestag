#!/usr/bin/python

from __future__ import print_function

import argparse
import sys
import json
import signal
from time import sleep

from gameState import GameState
from gameLogic import GameLogic
from serverConnection.listeningThread import ListeningThread
from player import Player
import proto

from api.restapi import RestApiThread

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='BraidsTag server.')
    parser.add_argument('-H', '--headless', action='store_true', help='start headless. There will be no UI although the REST API will still allow control')
    parser.add_argument('-a', '--appPath',  type=str, help='filesystem path of the admin webapp build. If specified, the app will be served on /.')

    args = parser.parse_args()

    gameState = GameState()
    gameLogic = GameLogic(gameState)

    main = ListeningThread(gameLogic)
    main.start()

    api = RestApiThread(gameState, gameLogic, main, args.appPath)
    api.start()

    def playerAdjusted(teamID, playerID, player, parameters):
        msg = proto.PLAYER_SNAPSHOT.create(json.dumps(player, cls=Player.Encoder))
        main.queueMessage(teamID, playerID, msg)

        msg = proto.PARAMETERS_SNAPSHOT.create(json.dumps(parameters.toSimpleTypes()))
        main.queueMessage(teamID, playerID, msg)

    def gameStarted():
        main.queueMessageToAll(proto.STARTGAME.create(gameState.gameTimeRemaining()))

    def gameStopped():
        main.queueMessageToAll(proto.STOPGAME.create())

    gameState.addListener(
        gameStarted=gameStarted,
        gameStopped=gameStopped,
        playerAdjusted=playerAdjusted
    )

    def exit_server(retval):
        def print_players(s):
            for i in s.players.values():
                print(i)
        gameState.withCurrGameState(print_players)

        main.stop()
        api.stop()

        sys.exit(retval)

    if not args.headless:
        from serverUi import MainWindow
        from PySide import QtGui

        # Create Qt application
        app = QtGui.QApplication(sys.argv)
        mainWindow = MainWindow(gameLogic, gameState, main)
        mainWindow.show()

        # Enter Qt main loop
        retval = app.exec_()

        exit_server(retval)
    else:
        signal.signal(signal.SIGINT, lambda x, y: exit_server(1))

        # kill time until we are interrupted.
        while True:
            sleep(3600)
