#!/usr/bin/python

from __future__ import print_function

import time
import os
from PySide.QtCore import Signal, QObject

class Player(QObject):

  def __init__(self, teamID, playerID):
    self.teamID = int(teamID)
    self.playerID = int(playerID)
    self.reset()

  def reset(self):
    self.ammo = 100
    self.maxAmmo = 100
    self.health = 5
    self.maxHealth = 8
    self.gunDamage = 1

  def __str__(self):
    return "Player(team=%d, id=%d, ammo=%d, health=%d)" % (self.teamID, self.playerID, self.ammo, self.health)

  def reduceHealth(self, damage):
    if (self.health > int(damage)):
      self.health -= int(damage)
    elif (self.health > 0):
      self.health = 0
    else:
      #already have 0 health
      pass


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

  def hit(self, gameState, toPlayer, fromPlayer, damage):
    if not gameState.isGameStarted():
      print("hit before game started")
      pass
      #TODO how does this happen, log this? client->server lag will trigger this
    elif (fromPlayer.playerID == toPlayer.playerID and fromPlayer.teamID == toPlayer.teamID):
      #self shot, ignore this
      pass
    elif fromPlayer.health <= 0:
      #shooting player is already dead, don't count this.
      pass
    else:
      toPlayer.reduceHealth(damage)

  def trigger(self, gameState, player):
    if not gameState.isGameStarted():
      return False
    if player.ammo > 0 and player.health > 0:
      player.ammo = player.ammo - 1
      return True
    else:
      return False

  def fullAmmo(self, gameState, player):
    retval = player.ammo != player.maxAmmo
    player.ammo = player.maxAmmo
    return retval

class ClientServer():
  PORT=int(os.getenv("PORT", "7079"))
  #SERVER="192.168.1.116"
  #SERVER="192.168.3.199"
  #SERVER="192.168.0.58"
  SERVER=os.getenv("SERVER", "192.168.1.151")
  #SERVER="127.0.0.1"
