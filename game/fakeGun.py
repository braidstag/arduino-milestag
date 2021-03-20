#!/usr/bin/python

from threading import Thread
import Queue

import proto
import client

from PySide import QtGui
QPushButton = QtGui.QPushButton
QWidget = QtGui.QWidget
QVBoxLayout = QtGui.QVBoxLayout
QHBoxLayout = QtGui.QHBoxLayout
QApplication = QtGui.QApplication
QLabel = QtGui.QLabel


class TriggerButton(QPushButton):
    def __init__(self, serial, label, triggerDown, triggerUp, parent=None):
        super(TriggerButton, self).__init__(label, parent)
        self.serial = serial
        self.triggerDown = triggerDown
        self.triggerUp = triggerUp
        self.clicked.connect(self.trigger)

    def trigger(self):
        if self.triggerDown:
            self.serial.queueMessage(proto.TRIGGER.create())
        if self.triggerUp:
            self.serial.queueMessage(proto.TRIGGER_RELEASE.create())


class ShotButton(QPushButton):
    def __init__(self, serial, teamID, playerID, parent=None):
        super(ShotButton, self).__init__(str(teamID) + ", " + str(playerID), parent)
        self.serial = serial
        self.teamID = teamID
        self.playerID = playerID
        self.clicked.connect(self.shot)

    def shot(self):
        self.serial.queueMessage(proto.HIT.create(self.teamID, self.playerID, 3))


class PlayerDetailsWidget(QWidget):
    def __init__(self, gameState, parent=None):
        super(PlayerDetailsWidget, self).__init__(parent)

        self.gameState = gameState
        self.gameState.addListener(
            currentStateChanged=self.__updateFromPlayer,
            connectionsChanged=self.__updateFromPlayer
        )

        layout = QHBoxLayout()

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
        player = self.gameState.getMainPlayer()
        if player:
            self.idLabel.setText("Team: %d, Player: %d" % (player.teamID, player.playerID))
            self.ammoLabel.setText("Ammo: %d" % player.ammo)
            self.healthLabel.setText("Health: %d / %d" % (player.health, self.gameState.getPlayerParameter(player, "maxHealth")))
        else:
            self.idLabel.setText("Team/Player: None - " + self.gameState.clientState)
            self.ammoLabel.setText("Ammo: 0")
            self.healthLabel.setText("Health: 0 / 0")


class MainWindow(QWidget):
    def __init__(self, serial, mainClient, parent=None):
        super(MainWindow, self).__init__(parent)
        self.serial = serial
        self.mainClient = mainClient

        self.setWindowTitle("BraidsTag Debugging Gun")
        layout = QVBoxLayout()

        playerDetails = PlayerDetailsWidget(mainClient.gameState)
        layout.addWidget(playerDetails)

        triggerLayout = QHBoxLayout()
        triggerLayout.addWidget(TriggerButton(self.serial, "trigger", True, True))
        triggerLayout.addWidget(TriggerButton(self.serial, "trigger Down", True, False))
        triggerLayout.addWidget(TriggerButton(self.serial, "trigger Up", False, True))
        layout.addLayout(triggerLayout)

        hLayout2 = QHBoxLayout()
        hLayout2.addWidget(ShotButton(self.serial, 0, 0))
        layout.addLayout(hLayout2)

        for i in range(1, 4):
            hLayout2 = QHBoxLayout()
            for j in range(1, 4):
                hLayout2.addWidget(ShotButton(self.serial, j, i))
            layout.addLayout(hLayout2)

        self.setLayout(layout)


class SerialAdapter():
    readQueue = Queue.Queue()
    shouldStop = False
    # Queue gets garbage collected while it is still being used when shutting down so keep a reference here
    empty = Queue.Empty

    def queueMessage(self, line):
        self.readQueue.put(line + "\n")

    def stop(self):
        self.shouldStop = True

    # # Writing

    def write(self, line):
        if line == "c\n":
            self.queueMessage("c")
        pass  # We don't react to anything else the pi tells us yet

    # # Reading

    def __iter__(self):
        return self

    def next(self):
        while not self.shouldStop:
            try:
                return self.readQueue.get(True, 5)
            except self.empty:
                continue

        # Stop the iteration
        raise StopIteration()

    def readline(self):
        return self.next()

    # # Misc

    def close(self):
        pass


class MainClientThread(Thread):
    def __init__(self, mainClient):
        super(MainClientThread, self).__init__(group=None)
        self.name = "Main Gun Client"
        self.mainClient = mainClient

    def run(self):
        mainClient.serialReadLoop()


if __name__ == "__main__":
    # load main in another thread, start the Qt event loop in this one.
    app = QApplication([])

    serial = SerialAdapter()

    mainClient = client.Client(serial)

    fakeGunWindow = MainWindow(serial, mainClient)
    fakeGunWindow.show()

    t = MainClientThread(mainClient)
    t.start()

    app.exec_()

    serial.stop()
