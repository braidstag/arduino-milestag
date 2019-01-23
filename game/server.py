#!/usr/bin/python

from __future__ import print_function

import argparse
import sys
import json

from gameState import GameState
from gameLogic import GameLogic
from serverConnection.listeningThread import ListeningThread
from serverUi import MainWindow
from player import Player
import proto

from PySide import QtGui

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='BraidsTag server.')
  args = parser.parse_args()

  gameState = GameState()
  gameLogic = GameLogic(gameState)

  main = ListeningThread(gameLogic)
  main.start()

  def playerAdjusted(teamID, playerID, player):
    msg = proto.SNAPSHOT.create(json.dumps(player, cls=Player.Encoder))
    main.queueMessage(teamID, playerID, msg)

  gameState.addListener(playerAdjusted = playerAdjusted)

  # Create Qt application
  app = QtGui.QApplication(sys.argv)
  mainWindow = MainWindow(gameLogic, gameState, main)
  mainWindow.show()

  # Enter Qt main loop
  retval = app.exec_()

  def printPlayers(s):
    for i in s.players.values():
      print(i)
  gameState.withCurrGameState(printPlayers)

  main.stop()

  sys.exit(retval)
