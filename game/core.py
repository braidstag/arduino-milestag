#!/usr/bin/python

import time
from PySide.QtCore import Signal, QObject

class Player():

  def __init__(self, teamID, playerID):
    self.teamID = int(teamID)
    self.playerID = int(playerID)
    self.reset()

  def reset(self):
    self.ammo = 100
    self.health = 5
    self.maxHealth = 8
    self.gunDamage = 1

  def __str__(self):
    return "Player(team=%d, id=%d, ammo=%d, health=%d)" % (self.teamID, self.playerID, self.ammo, self.health)

class GameState(QObject):
  def __init__(self):
    super(GameState, self).__init__()
    self.gameStartTime = None
    self.gameEndTime = None
    self.gameTime = 0

  def setGameTime(self, duration):
    self.gameTime = duration

  def startGame(self):
    self.gameStartTime = time.time()
    self.gameEndTime = time.time() + self.gameTime
    self.gameStarted.emit()

  def stopGame(self):
    self.gameStartTime = None
    self.gameEndTime = None
    self.gameStopped.emit()

  def isGameStarted(self):
    return self.gameEndTime and self.gameEndTime > time.time()

  def gameTimeRemaining(self):
    if (not self.gameEndTime) or (self.gameEndTime <= time.time()):
      return 0
    
    return int(self.gameEndTime - time.time())

  gameStarted = Signal()
  gameStopped = Signal()

class StandardGameLogic(QObject):

  def hit(self, gameState, toPlayer, fromTeam, fromPlayer, damage):
    if not gameState.isGameStarted():
      print("hit before game started")
      pass
      #TODO how does this happen, log this?
    elif (fromPlayer == toPlayer.playerID and fromTeam == toPlayer.teamID):
      #self shot, ignore this
      pass
    else:
      if (toPlayer.health > int(damage)):
        toPlayer.health -= int(damage)
      elif (toPlayer.health > 0):
        self.playerDead.emit()
        toPlayer.health = 0
      else:
        #already have 0 health
        pass

  def trigger(self, gameState, player):
    if not gameState.isGameStarted():
      return False
    if player.ammo > 0 and player.health > 0:
      player.ammo = player.ammo - 1
      return True
    else:
      return False

  playerDead = Signal()

class ClientServer():
  PORT=7079
  #SERVER="192.168.1.116"
  #SERVER="192.168.3.199"
  SERVER="192.168.1.151"
