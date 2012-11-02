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
      return self.gameState.players[indexTuple]

    return None

  def headerData(self, section, orientation, role  = Qt.DisplayRole):
    if role == Qt.DisplayRole:
      if orientation == Qt.Horizontal:
        return "Team %d" % (section + 1)
      else:
        return "%d" % (section + 1)

    return None

  def playerUpdated(self, teamIDStr, playerIDStr):
    teamID = int(teamIDStr)
    playerID = int(playerIDStr)
    self.dataChanged.emit(self.index(playerID, teamID, QModelIndex()), self.index(playerID, teamID, QModelIndex()))


class LinearModel(QAbstractListModel):
  def __init__(self, source):
    super(LinearModel, self).__init__()
    self.source = source
    self.source.dataChanged.connect(self.dataChangedDelegate)

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

class GameStartToggleButton(QPushButton):
  def __init__(self, gameState, parent=None):
    super(GameStartToggleButton, self).__init__("Start Game", parent)
    self.gameState = gameState
    self.clicked.connect(self.toggleGameStarted)
    self.gameStarted = False

  def toggleGameStarted(self):
    self.gameStarted = not self.gameStarted
    if self.gameStarted:
      self.gameState.startGame()
      self.setText("End Game")
    else:
      self.gameState.stopGame()
      self.setText("Start Game")


class PlayerDelegate(QStyledItemDelegate):
  def paint(self, painter, option, index):
    if index.data() == None:
      QStyledItemDelegate.paint(self, painter, option, index)
    else:
      painter.save()
      painter.setClipRect(option.rect)

      #NB. it might be easier to create a widget and call render on it
      ammoStr = str(index.data().ammo)
      painter.drawText(option.rect, ammoStr)

      painter.translate(option.rect.topLeft())

      ammoWidth = QFontMetrics(option.font).width("000") # allow space for 3 big digits
      ammoHeight = QFontMetrics(option.font).height()
      painter.setBrush(Qt.SolidPattern)
      painter.drawRoundedRect(ammoWidth + 5, 2, 100 * index.data().health / index.data().maxHealth, ammoHeight - 4, 5, 5)
      painter.setBrush(Qt.NoBrush)
      painter.drawRoundedRect(ammoWidth + 5, 2, 100, ammoHeight - 4, 5, 5)
      painter.restore()


class GameControl(QWidget):
  def __init__(self, gameState, parent=None):
    super(GameControl, self).__init__(parent)
    self.gameState = gameState

    layout = QVBoxLayout()

    gameStart = GameStartToggleButton(gameState)
    layout.addWidget(gameStart)

    teamCount = QSlider(Qt.Horizontal)
    teamCount.setMinimum(1)
    teamCount.setMaximum(8)
    teamCount.setSingleStep(1)
    teamCount.setPageStep(1)
    teamCount.setTickPosition(QSlider.TicksAbove)
    teamCount.setTickInterval(1)
    teamCount.setValue(self.gameState.targetTeamCount)
    teamCount.valueChanged.connect(self.gameState.setTargetTeamCount)

    layout.addWidget(teamCount)

    self.setLayout(layout)

class MainWindow(QWidget):
  def __init__(self, gameState, parent=None):
    super(MainWindow, self).__init__(parent)
    self.setWindowTitle("BraidsTag Server")

    layout = QVBoxLayout()
    tabs = QTabWidget(self)

    gameControl = GameControl(gameState)
    tabs.addTab(gameControl, "Control")

    #self.model = LinearModel(GameStateModel(gameState))
    #listView = QListView()
    #listView.setModel(self.model)
    #layout.addWidget(listView)
    #tabs.addTab(listView, "Players")

    self.model = GameStateModel(gameState)
    listView = QTableView()
    listView.setModel(self.model)
    listView.setItemDelegate(PlayerDelegate())
    #layout.addWidget(listView)
    tabs.addTab(listView, "Players")

    self.log = QTextEdit()
    #self.log.document().setMaximumBlockCount(10)
    self.log.setReadOnly(True)
    tabs.addTab(self.log, "Log")

    layout.addWidget(tabs)

    self.setLayout(layout)

  def playerUpdated(self, teamID, playerID):
    self.model.playerUpdated(teamID, playerID)

  def  playerAdded(self, sentTeam, sentPlayer):
    self.model.layoutChanged.emit(); #TODO: this is a bit of a blunt instrument.

  def lineReceived(self, line):
    self.log.append(line.strip())
    #TODO: auto-scroll to the bottom
    #sb = self.log.verticalScrollBar()
    #sb.setValue(sb.maximum())
