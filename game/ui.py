#!/usr/bin/python

import argparse
import re
import socket
import sys
from threading import Thread, Lock

from core import Player, StandardGameLogic, ClientServer

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtDeclarative import QDeclarativeView

class GameStateModel(QAbstractTableModel):
  """
  A Model which represents the players' gameState. The team is the column and the player is the row.
  """

  def __init__(self, gameState):
    super(GameStateModel, self).__init__()
    self.gameState = gameState

  def rowCount(self, index):
    return self.gameState.largestTeam

  def columnCount(self, index):
    return self.gameState.teamCount

  def data(self, index, role = Qt.DisplayRole):
    if not index.isValid():
      return None

    if role == Qt.DisplayRole:
      indexTuple = (index.column() + 1, index.row() + 1)
      if indexTuple not in self.gameState.players:
        return None
      return str(self.gameState.players[indexTuple])

    return None

  def playerUpdated(self, teamIDStr, playerIDStr):
    teamID = int(teamIDStr)
    playerID = int(playerIDStr)
    self.dataChanged.emit(self.index(playerID, teamID, QModelIndex()), self.index(playerID, teamID, QModelIndex()))


class LinearModel(QAbstractListModel):
  def __init__(self, source):
    super(LinearModel, self).__init__()
    self.source = source
    QObject.connect(self.source, SIGNAL('dataChanged()'), self.dataChangedDelegate)

  def rowCount(self, index):
    return self.source.rowCount(index) * self.source.columnCount(index)

  def columnCount(self, index):
    return 1

  def data(self, index, role = Qt.DisplayRole):
    return self.source.data(self.source.index(index.row() % self.source.columnCount(index.parent()), index.row() // self.source.columnCount(index.parent()), index.parent()), role)

  def dataChangedDelegate(self, startIndex, endIndex):
    self.dataChanged.emit(self.index(0, startIndex.row() * startIndex.column(), QModelIndex()), self.index(0, endIndex.row() * endIndex.column(), QModelIndex()))

  def playerUpdated(self, teamID, playerID):
    self.source.playerUpdated(teamID, playerID)

class MainWindow(QDialog):
  def __init__(self, gameState, parent=None):
    super(MainWindow, self).__init__(parent)
    self.setWindowTitle("BraidsTag Server")

    self.layout = QVBoxLayout()
    self.listModel = LinearModel(GameStateModel(gameState))
    self.listView = QListView()
    self.listView.setModel(self.listModel)
    self.layout.addWidget(self.listView)

    self.setLayout(self.layout)

  def playerUpdated(self, teamID, playerID):
    self.listModel.playerUpdated(teamID, playerID)

  def  playerAdded(self, sentTeam, sentPlayer):
    self.listModel.layoutChanged.emit(); #TODO: this is a bit of a blunt instrument.
