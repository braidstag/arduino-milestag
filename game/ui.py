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
    #TODO: I think this is called with 1-based numbers, shouldn't it be 0-based when emitted?
    self.dataChanged.emit(self.index(playerID, teamID, QModelIndex()), self.index(playerID, teamID, QModelIndex()))

  #DnD support
  def setData(self, index, value, role = Qt.EditRole):
    if not index.isValid() or index.column() >= self.gameState.teamCount:
      return False
    if value == None:
      return False
    
    #move all the other players down
    lowestBlank = self.gameState.largestTeam

    for playerID in range(index.row(), self.gameState.largestTeam + 1):
      if (index.column() + 1, playerID + 1) not in self.gameState.players:
        lowestBlank = playerID
        break

    for playerID in range(lowestBlank, index.row(), -1):
      self.gameState.movePlayer(index.column() + 1, playerID, index.column() + 1, playerID + 1)

    oldTeamID = value.teamID
    oldPlayerID = value.playerID
    self.gameState.movePlayer(oldTeamID, oldPlayerID, index.column() + 1, index.row() + 1)
    self.dataChanged.emit(self.index(index.row(), index.column(), QModelIndex()), self.index(self.gameState.largestTeam - 1, index.column(), QModelIndex()))
    self.dataChanged.emit(self.index(oldTeamID - 1, oldPlayerID - 1, QModelIndex()), self.index(oldTeamID - 1, oldPlayerID - 1, QModelIndex()))
    self.layoutChanged.emit() #TODO
    return True

  def flags(self, index):
    return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

  def supportedDropActions(self):
     return Qt.CopyAction | Qt.MoveAction


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


class GameResetButton(QPushButton):
  def __init__(self, gameState, parent=None):
    super(GameResetButton, self).__init__("Reset", parent)
    self.gameState = gameState
    self.clicked.connect(self.reset)

  def reset(self):
    self.gameState.resetGame()

  def toggleEnabled(self):
    self.setEnabled(not self.isEnabled())


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

  def sizeHint(self, option, index):
    return QSize(150, 20)


class LabelledSlider(QWidget):
  def __init__(self, label):
    super(LabelledSlider, self).__init__()
    layout = QHBoxLayout()
    self.slider = QSlider(Qt.Horizontal)
    self.staticLabel = QLabel(label)
    self.valueLabel = QLabel()
    self.updateValueLabel(self.slider.value())
    self.slider.valueChanged.connect(self.updateValueLabel)

    layout.addWidget(self.staticLabel)
    layout.addWidget(self.valueLabel)
    layout.addWidget(self.slider)

    self.setLayout(layout)

  def formatValue(self, value):
    "A method for formatting the slider's int value into a label. This should be overridden if you don't just want str()"
    return str(value)

  def updateValueLabel(self, value):
    self.valueLabel.setText(self.formatValue(value))

class TeamCountSlider(LabelledSlider):
  def __init__(self, gameState):
    super(TeamCountSlider, self).__init__("Team Size: ")

    self.slider.setMinimum(1)
    self.slider.setMaximum(8)
    self.slider.setSingleStep(1)
    self.slider.setPageStep(1)
    self.slider.setTickPosition(QSlider.TicksAbove)
    self.slider.setTickInterval(1)
    self.slider.setValue(gameState.targetTeamCount)
    self.slider.valueChanged.connect(gameState.setTargetTeamCount)


class GameTimeSlider(LabelledSlider):
  def __init__(self, gameState):
    super(GameTimeSlider, self).__init__("Game Time: ")

    self.slider.setMinimum(60) # 1 minute
    self.slider.setMaximum(1800) # 30 minutes
    self.slider.setSingleStep(60) # 1 minute
    self.slider.setPageStep(300) # 5 minutes
    self.slider.setTickPosition(QSlider.TicksAbove)
    self.slider.setTickInterval(300)
    self.slider.setValue(gameState.gameTime)
    self.slider.valueChanged.connect(gameState.setGameTime)

  def formatValue(self, value):
    return str(value // 60) + ":" + str(value % 60)

class GameControl(QWidget):
  def __init__(self, gameState, parent=None):
    super(GameControl, self).__init__(parent)
    self.gameState = gameState

    layout = QVBoxLayout()

    gameStart = GameStartToggleButton(gameState)
    layout.addWidget(gameStart)

    gameReset = GameResetButton(gameState)
    layout.addWidget(gameReset)
    gameStart.clicked.connect(gameReset.toggleEnabled)

    #hLayout = QHBoxLayout()

    teamCount = TeamCountSlider(self.gameState)
    #hLayout.addWidget(teamCount)
    layout.addWidget(teamCount)

    gameTime = GameTimeSlider(self.gameState)
    #hLayout.addWidget(gameTime)
    layout.addWidget(gameTime)

    #layout.addWidget(hLayout)

    self.setLayout(layout)


class MainWindow(QWidget):
  def __init__(self, gameState, parent=None):
    super(MainWindow, self).__init__(parent)
    gameState.addPlayerUpdateListener(self)

    self.setWindowTitle("BraidsTag Server")
    layout = QVBoxLayout()
    tabs = QTabWidget(self)

    gameControl = GameControl(gameState)
    tabs.addTab(gameControl, "&1. Control")

    self.model = GameStateModel(gameState)
    tableView = QTableView()
    tableView.setModel(self.model)
    tableView.setItemDelegate(PlayerDelegate())
    tableView.setSelectionMode(QAbstractItemView.SingleSelection);
    tableView.setDragEnabled(True)
    tableView.setAcceptDrops(True)
    tableView.setDropIndicatorShown(True);
    tableView.setDragDropMode(QAbstractItemView.InternalMove);
    self.model.layoutChanged.connect(tableView.resizeColumnsToContents)
    tabs.addTab(tableView, "&2. Players")

    self.log = QTextEdit()
    #self.log.document().setMaximumBlockCount(10)
    self.log.setReadOnly(True)
    tabs.addTab(self.log, "&3. Log")

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
