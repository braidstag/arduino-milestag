#!/usr/bin/python

import argparse
import re
import socket
import sys
from threading import Thread, Lock
from time import time

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
    self.gameState.playerUpdated.connect(self.playerChanged)
    self.gameState.playerAdded.connect(self.playerChanged)
    self.gameState.playerDeleted.connect(self.playerChanged)

    self.gameState.playerMoved.connect(self.playerMoved)
    
    self.gameState.largestTeamChanged.connect(self.playerLayoutChanged)
    self.gameState.teamCountChanged.connect(self.playerLayoutChanged)

  #
  # Getters
  #
  def rowCount(self, index):
    return self.gameState.largestTeam + 1

  def columnCount(self, index):
    return self.gameState.teamCount + 1

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

  #
  # Slots
  #
  def playerChanged(self, teamID, playerID):
    self.dataChanged.emit(self.index(playerID - 1, teamID - 1, QModelIndex()), self.index(playerID - 1, teamID - 1, QModelIndex()))

  def playerMoved(self, srcTeamID, srcPlayerID, dstTeamID, dstPlayerID):
    self.playerChanged(srcTeamID, srcPlayerID)
    self.playerChanged(dstTeamID, dstPlayerID)

  def playerLayoutChanged(self, _):
    self.layoutChanged.emit()

  #
  #DnD support
  #
  def setData(self, index, value, role = Qt.EditRole):
    if not index.isValid():
      return False

    if value == None:
      self.gameState.deletePlayer(index.column() + 1, index.row() + 1)
      return True
    
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
    self.gameState.gameStarted.connect(self.gameStarted)
    self.gameState.gameStopped.connect(self.gameStopped)

  def toggleGameStarted(self):
    if not self.gameState.isGameStarted():
      self.gameState.startGame()
    else:
      self.gameState.stopGame()

  def gameStarted(self):
    self.setText("End Game")

  def gameStopped(self):
    self.setText("Start Game")


class GameTimeLabel(QLabel):
  def __init__(self, gameState, parent=None):
    super(GameTimeLabel, self).__init__("--:--", parent)
    self.gameState = gameState
    self.gameState.gameStarted.connect(self.gameStarted)
    self.gameState.gameStopped.connect(self.gameStopped)
    self.gameTimeLabelTimer = None

  def gameStarted(self):
    self.gameTimeLabelTimer = QTimer()
    self.gameTimeLabelTimer.timeout.connect(self.updateGameTimeLabel)
    self.gameTimeLabelTimer.start(1000)
    self.updateGameTimeLabel()

  def gameStopped(self):
    self.setText("--:--")
    if self.gameTimeLabelTimer:
      self.gameTimeLabelTimer.stop()
    self.gameTimeLabelTimer = None

  def updateGameTimeLabel(self):
    toGo = max(0, self.gameState.gameEndTime - time())
    self.setText("%02d:%02d" % ((toGo // 60),  (toGo % 60)))


class GameResetButton(QPushButton):
  def __init__(self, gameState, parent=None):
    super(GameResetButton, self).__init__("Reset", parent)
    self.gameState = gameState
    self.clicked.connect(self.reset)
    self.gameState.gameStarted.connect(self.gameStarted)
    self.gameState.gameStopped.connect(self.gameStopped)

  def reset(self):
    self.gameState.resetGame()

  def gameStarted(self):
    self.setEnabled(False)

  def gameStopped(self):
    self.setEnabled(True)


class PlayerDelegate(QStyledItemDelegate):
  def paint(self, painter, option, index):
    if index.data() == None:
      QStyledItemDelegate.paint(self, painter, option, index)
    else:
      painter.save()
      painter.setClipRect(option.rect)

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
    return "%02d:%02d" % ((value // 60),  (value % 60))

class GameControl(QWidget):
  def __init__(self, gameState, parent=None):
    super(GameControl, self).__init__(parent)
    self.gameState = gameState

    layout = QVBoxLayout()
    hLayout = QHBoxLayout()

    gameTimeLabel = GameTimeLabel(gameState)
    hLayout.addWidget(gameTimeLabel)

    gameStart = GameStartToggleButton(gameState)
    hLayout.addWidget(gameStart)

    gameReset = GameResetButton(gameState)
    hLayout.addWidget(gameReset)

    layout.addLayout(hLayout)

    teamCount = TeamCountSlider(self.gameState)
    layout.addWidget(teamCount)

    gameTime = GameTimeSlider(self.gameState)
    layout.addWidget(gameTime)

    self.setLayout(layout)


class PlayerDetailsWidget(QWidget):
  def __init__(self, gameState, parent=None):
    super(PlayerDetailsWidget, self).__init__(parent)

    self.gameState = gameState
    self.gameState.playerAdded.connect(self.playerUpdated)
    self.gameState.playerDeleted.connect(self.playerUpdated)
    self.gameState.playerUpdated.connect(self.playerUpdated)
    self.gameState.playerMoved.connect(self.playerMoved)

    layout = QVBoxLayout()

    self.idLabel = QLabel("")
    layout.addWidget(self.idLabel)

    self.ammoLabel = QLabel("")
    layout.addWidget(self.ammoLabel)

    self.healthLabel = QLabel("")
    layout.addWidget(self.healthLabel)

    self.playerID = None
    self.teamID = None

    self.__updateFromPlayer()

    self.setLayout(layout)

  def __updateFromPlayer(self):
    if (self.teamID, self.playerID) in self.gameState.players:
      player = self.gameState.getOrCreatePlayer(self.teamID, self.playerID)
      self.idLabel.setText("%d:%d" % (player.teamID, player.playerID))
      self.ammoLabel.setText(str(player.ammo))
      self.healthLabel.setText("%d / %d" % (player.health, player.maxHealth))
    else:
      self.idLabel.setText("None")
      self.ammoLabel.setText("0")
      self.healthLabel.setText("0 / 0")


  def playerUpdated(self, teamID, playerID):
    if self.teamID and self.teamID == teamID and self.playerID == playerID:
      #update our display
      self.__updateFromPlayer()

  def playerMoved(self, fromTeam, fromPlayer, toeam, toPlayer):
    self.playerUpdated(fromTeam, fromPlayer)

  def currentChanged(self, selected, deselected):
    self.teamID = selected.column() + 1
    self.playerID = selected.row() + 1
    self.__updateFromPlayer()


class TrashDropTarget(QLabel):
  def __init__(self, parent=None):
    super(TrashDropTarget, self).__init__("Trash", parent)
    self.setAcceptDrops(True)

  def dragEnterEvent(self, event):
    event.acceptProposedAction()

  def dropEvent(self, event):
    event.acceptProposedAction()


class PlayersView(QWidget):
  def __init__(self, model, gameState, parent=None):
    super(PlayersView, self).__init__(parent)
    self.model = model

    layout = QVBoxLayout()
    splitter = QSplitter()
    layout.addWidget(splitter)

    #This is ugly, is there a better way?!
    tableLayout = QVBoxLayout()
    tableLayoutWidget = QWidget()
    tableLayoutWidget.setLayout(tableLayout)
    splitter.addWidget(tableLayoutWidget)

    trashLabel = TrashDropTarget()
    tableLayout.addWidget(trashLabel)

    tableView = QTableView()
    tableView.setModel(self.model)
    tableView.setItemDelegate(PlayerDelegate())
    tableView.setSelectionMode(QAbstractItemView.SingleSelection)
    tableView.setDragEnabled(True)
    tableView.setAcceptDrops(True)
    tableView.setDropIndicatorShown(True)
    #enable drag and drop but only accept things locally (still allows dragging them out though)
    tableView.setDragDropMode(QAbstractItemView.DragDrop)
    tableView.setDefaultDropAction(Qt.MoveAction)
    self.model.layoutChanged.connect(tableView.resizeColumnsToContents)

    tableLayout.addWidget(tableView)

    self.detailWidget = PlayerDetailsWidget(gameState)
    splitter.addWidget(self.detailWidget)

    sm = tableView.selectionModel() #This line is needed on windows (and possibly others). I have no idea why!
    tableView.selectionModel().currentChanged.connect(self.detailWidget.currentChanged)

    self.setLayout(layout)


class MainWindow(QWidget):
  def __init__(self, gameState, parent=None):
    super(MainWindow, self).__init__(parent)
    self.model = GameStateModel(gameState)

    self.setWindowTitle("BraidsTag Server")
    layout = QVBoxLayout()
    tabs = QTabWidget(self)

    gameControl = GameControl(gameState)
    tabs.addTab(gameControl, "&1. Control")

    players = PlayersView(self.model, gameState)
    tabs.addTab(players, "&2. Players")

    self.log = QTextEdit()
    #self.log.document().setMaximumBlockCount(10)
    self.log.setReadOnly(True)
    tabs.addTab(self.log, "&3. Log")

    layout.addWidget(tabs)
    self.setLayout(layout)

  def lineReceived(self, line):
    self.log.append(line.strip())
    #TODO: auto-scroll to the bottom
    #sb = self.log.verticalScrollBar()
    #sb.setValue(sb.maximum())
