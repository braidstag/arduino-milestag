#!/usr/bin/python

import re
from time import time

# from PySide.QtCore import Qt #Why does pylint not like this?!
from PySide import QtCore
# from PySide.QtGui import QAbstractTableModel, QModelIndex, QPushButton, QLabel, QTimer, QStyledItemDelegate, QWidget, QVBoxLayout, QSplitter, QFontMetrics, QPoint
from PySide import QtGui

Qt = QtCore.Qt
QAbstractTableModel = QtCore.QAbstractTableModel
QModelIndex = QtCore.QModelIndex
QPoint = QtCore.QPoint
QSize = QtCore.QSize
QTimer = QtCore.QTimer
Signal = QtCore.Signal

QAbstractItemView = QtGui.QAbstractItemView
QFontMetrics = QtGui.QFontMetrics
QHBoxLayout = QtGui.QHBoxLayout
QLabel = QtGui.QLabel
QPushButton = QtGui.QPushButton
QSlider = QtGui.QSlider
QSplitter = QtGui.QSplitter
QStyledItemDelegate = QtGui.QStyledItemDelegate
QTableView = QtGui.QTableView
QTabWidget = QtGui.QTabWidget
QTextEdit = QtGui.QTextEdit
QVBoxLayout = QtGui.QVBoxLayout
QWidget = QtGui.QWidget


class GameStateModel(QAbstractTableModel):
    """
    A Model which represents the current gameState. The team is the column and the player is the row.
    """

    def __init__(self, gameState):
        super(GameStateModel, self).__init__()
        self.gameState = gameState

        self.gameState.addListener(currentStateChanged=self.gameStateChanged)

    #
    # Getters
    #
    def rowCount(self, _index):
        return self.gameState.withCurrGameState(lambda s: s.largestTeam + 1)

    def columnCount(self, _index):
        return self.gameState.withCurrGameState(lambda s: s.teamCount + 1)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            indexTuple = (index.column() + 1, index.row() + 1)
            if indexTuple not in self.gameState.withCurrGameState(lambda s: s.players.keys()):
                return None
            return self.gameState.withCurrGameState(lambda s: s.players[indexTuple])

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return "Team %d" % (section + 1)
            else:
                return "%d" % (section + 1)

        return None

    def gameStateChanged(self):
        self.dataChanged.emit(self.index(0, 0, QModelIndex()), self.index(self.gameState.withCurrGameState(lambda s: s.largestTeam), self.gameState.withCurrGameState(lambda s: s.teamCount), QModelIndex()))
        self.layoutChanged.emit()

    #
    # DnD support
    #
    def setData(self, index, value, _role=Qt.EditRole):
        if not index.isValid():
            return False

        if value is None:
            # TODO: do we call this on gameState or listeningThread
            self.gameState.deletePlayer(index.column() + 1, index.row() + 1)
            return True

        # move all the other players down
        def findLowestBlank(currGameState):
            lowest_blank = currGameState.largestTeam

            for player_id in range(index.row(), currGameState.largestTeam + 1):
                if (index.column() + 1, player_id + 1) not in currGameState.players:
                    lowest_blank = player_id
                    break
            return lowest_blank
        lowestBlank = self.gameState.withCurrGameState(findLowestBlank)

        for player_id in range(lowestBlank, index.row(), -1):
            # TODO: do we call this on gameState or listeningThread
            self.gameState.movePlayer(index.column() + 1, player_id, index.column() + 1, player_id + 1)

        old_team_id = value.team_id
        old_player_id = value.player_id
        # TODO: do we call this on gameState or listeningThread
        self.gameState.movePlayer(old_team_id, old_player_id, index.column() + 1, index.row() + 1)
        return True

    def flags(self, index):
        indexTuple = (index.column() + 1, index.row() + 1)
        if index.isValid() and indexTuple in self.gameState.withCurrGameState(lambda s: s.players.keys()):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction


class GameStartToggleButton(QPushButton):
    def __init__(self, gameLogic, gameState, parent=None):
        super(GameStartToggleButton, self).__init__("Start Game", parent)
        self.gameLogic = gameLogic
        self.gameState = gameState
        self.clicked.connect(self.toggleGameStarted)
        self.gameState.addListener(gameStarted=self.gameStarted, gameStopped=self.gameStopped)

    def toggleGameStarted(self):
        if not self.gameState.isGameStarted():
            self.gameLogic.startGame(time())
        else:
            self.gameLogic.stopGame(time())

    def gameStarted(self):
        self.setText("End Game")

    def gameStopped(self):
        self.setText("Start Game")


class GameTimeLabel(QLabel):
    def __init__(self, gameState, parent=None):
        super(GameTimeLabel, self).__init__("--:--", parent)
        self.gameState = gameState
        self.gameState.addListener(gameStarted=self.gameStarted, gameStopped=self.gameStopped)
        self.gameTimeLabelTimer = None
        self.startTimer.connect(self.startTimerSlot)
        self.stopTimer.connect(self.stopTimerSlot)

    def gameStarted(self):
        self.startTimer.emit()
        self.updateGameTimeLabel()

    def gameStopped(self):
        self.setText("--:--")
        self.stopTimer.emit()

    def updateGameTimeLabel(self):
        toGo = max(0, self.gameState.gameTimeRemaining())
        self.setText("%02d:%02d" % ((toGo // 60),  (toGo % 60)))

    # Make sure timers are started and stopped on the same thread.
    startTimer = Signal()
    stopTimer = Signal()

    def stopTimerSlot(self):
        if self.gameTimeLabelTimer:
            self.gameTimeLabelTimer.stop()
        self.gameTimeLabelTimer = None

    def startTimerSlot(self):
        self.gameTimeLabelTimer = QTimer()
        self.gameTimeLabelTimer.timeout.connect(self.updateGameTimeLabel)
        self.gameTimeLabelTimer.start(1000)


class GameResetButton(QPushButton):
    def __init__(self, gameLogic, gameState, parent=None):
        super(GameResetButton, self).__init__("Reset", parent)
        self.gameState = gameState
        self.gameLogic = gameLogic
        self.clicked.connect(self.reset)
        self.gameState.addListener(gameStarted=self.gameStarted, gameStopped=self.gameStopped)

    def reset(self):
        self.gameLogic.resetGame(time())

    def gameStarted(self):
        self.setEnabled(False)

    def gameStopped(self):
        self.setEnabled(True)


class PlayerDelegate(QStyledItemDelegate):
    def __init__(self, gameState, listeningThread):
        super(PlayerDelegate, self).__init__()
        self.listeningThread = listeningThread
        self.gameState = gameState

    def paint(self, painter, option, index):
        player = index.data()
        if player is None:
            QStyledItemDelegate.paint(self, painter, option, index)
        else:
            painter.save()
            painter.setClipRect(option.rect)

            ammoStr = str(player.ammo)
            painter.drawText(option.rect, ammoStr)

            painter.translate(option.rect.topLeft())

            ammoWidth = QFontMetrics(option.font).width("000")  # allow space for 3 big digits
            ammoHeight = QFontMetrics(option.font).height()
            painter.setBrush(Qt.SolidPattern)
            painter.drawRoundedRect(ammoWidth + 5, 2, 100 * player.health / self.gameState.getPlayerParameter(player, "maxHealth"), ammoHeight - 4, 5, 5)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(ammoWidth + 5, 2, 100, ammoHeight - 4, 5, 5)

            # TODO
            # if self.listeningThread.connections[(player.teamID, player.playerID)].isOutOfContact():
            #   triangleStart = ammoWidth + 5 + 100 + 5
            #   painter.drawConvexPolygon([QPoint(triangleStart, ammoHeight - 4), QPoint(triangleStart + (ammoHeight // 2), 2), QPoint(triangleStart + ammoHeight, ammoHeight - 4),])
            #   painter.drawText(triangleStart + (ammoHeight // 2) - 2, ammoHeight - 4, "!")

            painter.restore()

    def sizeHint(self, _option, _index):
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
        """A method for formatting the slider's int value into a label. This should be overridden if you don't just want str()"""
        return str(value)

    def updateValueLabel(self, value):
        self.valueLabel.setText(self.formatValue(value))


class TeamCountSlider(LabelledSlider):
    def __init__(self, gameState):
        super(TeamCountSlider, self).__init__("Team Size: ")

        self.gameState = gameState

        self.slider.setMinimum(1)
        self.slider.setMaximum(8)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(1)
        self.slider.setTickPosition(QSlider.TicksAbove)
        self.slider.setTickInterval(1)
        self.update()
        self.slider.valueChanged.connect(gameState.setTargetTeamCount)
        gameState.addListener(currentStateChanged=self.update)

    def update(self):
        self.slider.setValue(self.gameState.withCurrGameState(lambda s: s.targetTeamCount))


class GameTimeSlider(LabelledSlider):
    def __init__(self, gameState):
        super(GameTimeSlider, self).__init__("Game Time: ")
        self.gameState = gameState

        self.slider.setMinimum(60)  # 1 minute
        self.slider.setMaximum(1800)  # 30 minutes
        self.slider.setSingleStep(60)  # 1 minute
        self.slider.setPageStep(300)  # 5 minutes
        self.slider.setTickPosition(QSlider.TicksAbove)
        self.slider.setTickInterval(300)
        self.update()
        self.slider.valueChanged.connect(gameState.setGameTime)
        gameState.addListener(currentStateChanged=self.update)

    def update(self):
        self.slider.setValue(self.gameState.withCurrGameState(lambda s: s.gameTime))

    def formatValue(self, value):
        return "%02d:%02d" % ((value // 60),  (value % 60))


class GameControl(QWidget):
    def __init__(self, gameLogic, gameState, parent=None):
        super(GameControl, self).__init__(parent)
        self.gameState = gameState

        layout = QVBoxLayout()
        hLayout = QHBoxLayout()

        gameTimeLabel = GameTimeLabel(gameState)
        hLayout.addWidget(gameTimeLabel)

        gameStart = GameStartToggleButton(gameLogic, gameState)
        hLayout.addWidget(gameStart)

        gameReset = GameResetButton(gameLogic, gameState)
        hLayout.addWidget(gameReset)

        layout.addLayout(hLayout)

        teamCount = TeamCountSlider(self.gameState)
        layout.addWidget(teamCount)

        gameTime = GameTimeSlider(self.gameState)
        layout.addWidget(gameTime)

        self.setLayout(layout)


class PlayerDetailsWidget(QWidget):
    def __init__(self, gameState, listeningThread, parent=None):
        super(PlayerDetailsWidget, self).__init__(parent)

        self.listeningThread = listeningThread
        self.gameState = gameState
        self.gameState.addListener(self.gameStateChanged)

        layout = QVBoxLayout()

        self.idLabel = QLabel("")
        layout.addWidget(self.idLabel)

        self.ammoLabel = QLabel("")
        layout.addWidget(self.ammoLabel)

        self.healthLabel = QLabel("")
        layout.addWidget(self.healthLabel)

        self.warningLabel = QLabel("")
        layout.addWidget(self.warningLabel)

        self.playerID = None
        self.teamID = None

        self.__updateFromPlayer()

        self.setLayout(layout)

    def __updateFromPlayer(self):
        if (self.teamID, self.playerID) in self.gameState.withCurrGameState(lambda s: s.players.keys()):
            player = self.gameState.getOrCreatePlayer(self.teamID, self.playerID)
            self.idLabel.setText("Team: %d, Player: %d" % (player.team_id, player.player_id))
            self.ammoLabel.setText("Ammo: %d" % player.ammo)
            self.healthLabel.setText("%d / %d" % (player.health, self.gameState.getPlayerParameter(player, "maxHealth")))
            try:
                if self.listeningThread.connections[(player.teamID, player.playerID)].isOutOfContact():
                    self.warningLabel.setText("WARNING: This player has been out\nof contact for at least %s" % self.listeningThread.connections[(player.teamID, player.playerID)].outOfContactTimeStr())
                else:
                    self.warningLabel.setText("")
            except KeyError:
                self.warningLabel.setText("WARNING: This player is disconnected")
        else:
            self.idLabel.setText("None")
            self.ammoLabel.setText("0")
            self.healthLabel.setText("0 / 0")
            self.warningLabel.setText("")

    def gameStateChanged(self):
        self.__updateFromPlayer()

    def currentChanged(self, selected, _deselected):
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


class InitialisationButton(QPushButton):
    def __init__(self, gameState, listeningThread, parent=None):
        super(InitialisationButton, self).__init__("Initialise", parent)
        self.gameState = gameState
        self.listeningThread = listeningThread
        self.clicked.connect(self.initialise)
        self.gameState.addListener(connectionsChanged=self.refresh)

        self.refresh()

    def initialise(self):
        connection = self.listeningThread.uninitialisedConnections.pop()
        self.listeningThread.startInitialising(connection)

    def refresh(self):
        self.setEnabled(bool(not self.listeningThread.initialisingConnection and self.listeningThread.uninitialisedConnections))


class PlayersView(QWidget):
    def __init__(self, model, gameState, listeningThread, parent=None):
        super(PlayersView, self).__init__(parent)
        self.model = model

        layout = QVBoxLayout()
        splitter = QSplitter()
        layout.addWidget(splitter)

        # This is ugly, is there a better way?!
        tableLayout = QVBoxLayout()
        tableLayoutWidget = QWidget()
        tableLayoutWidget.setLayout(tableLayout)
        splitter.addWidget(tableLayoutWidget)

        trashLabel = TrashDropTarget()
        tableLayout.addWidget(trashLabel)

        initialisatonLabel = InitialisationButton(gameState, listeningThread)
        tableLayout.addWidget(initialisatonLabel)

        tableView = QTableView()
        tableView.setModel(self.model)
        tableView.setItemDelegate(PlayerDelegate(gameState, listeningThread))
        tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        tableView.setDragEnabled(True)
        tableView.setAcceptDrops(True)
        tableView.setDropIndicatorShown(True)
        # enable drag and drop but only accept things locally (still allows dragging them out though)
        tableView.setDragDropMode(QAbstractItemView.DragDrop)
        tableView.setDefaultDropAction(Qt.MoveAction)
        self.model.layoutChanged.connect(tableView.resizeColumnsToContents)

        tableLayout.addWidget(tableView)

        self.detailWidget = PlayerDetailsWidget(gameState, listeningThread)
        splitter.addWidget(self.detailWidget)

        # This line is needed on windows (and possibly others). I have no idea why!
        sm = tableView.selectionModel()  # pylint:disable=W0612
        tableView.selectionModel().currentChanged.connect(self.detailWidget.currentChanged)

        self.setLayout(layout)


class MainWindow(QWidget):
    def __init__(self, gameLogic, gameState, listeningThread, parent=None):
        super(MainWindow, self).__init__(parent)
        self.model = GameStateModel(gameState)

        self.setWindowTitle("BraidsTag Server")
        layout = QVBoxLayout()
        tabs = QTabWidget(self)

        gameControl = GameControl(gameLogic, gameState)
        tabs.addTab(gameControl, "&1. Control")

        players = PlayersView(self.model, gameState, listeningThread)
        tabs.addTab(players, "&2. Players")

        self.log = QTextEdit()
        # self.log.document().setMaximumBlockCount(10)
        self.log.setReadOnly(True)
        tabs.addTab(self.log, "&3. Log")

        layout.addWidget(tabs)
        self.setLayout(layout)

    def lineReceived(self, line):
        self.log.append(str(line).strip())
        # TODO: auto-scroll to the bottom
        # sb = self.log.verticalScrollBar()
        # sb.setValue(sb.maximum())
