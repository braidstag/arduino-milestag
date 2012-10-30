#!/usr/bin/python

import time

class Player():
  teamID = 0
  playerID = 0
  ammo = 100
  health = 5
  maxHealth = 8
  gunDamage = 1

  def __init__(self, teamID, playerID):
    self.teamID = int(teamID)
    self.playerID = int(playerID)

  def __str__(self):
    return "Player(team=%d, id=%d, ammo=%d, health=%d)" % (self.teamID, self.playerID, self.ammo, self.health)

class GameState():
  def __init__(self):
    self.gameStartTime = None
    self.gameEndTime = None

  def startGame(self, duration):
    self.gameStartTime = time.time()
    self.gameEndTime = time.time() + duration

  def stopGame(self):
    self.gameStartTime = None
    self.gameEndTime = None

  def isGameStarted(self):
    return self.gameEndTime and self.gameEndTime > time.time()

  def gameTimeRemaining(self):
    if (not self.gameEndTime) or (self.gameEndTime <= time.time()):
      return 0
    
    return int(self.gameEndTime - time.time())

class DefaultCallback():
  def playerDead(self):
    pass

class StandardGameLogic():
  def __init__(self, callback = DefaultCallback()):
    self.callback = callback

  def hit(self, gameState, toPlayer, fromTeam, fromPlayer, damage):
    if not gameState.isGameStarted():
      pass
      #TODO how does this happen, log this?
    elif (fromPlayer == toPlayer.playerID and fromTeam == toPlayer.teamID):
      #self shot, ignore this
      pass
    else:
      if (toPlayer.health > int(damage)):
        toPlayer.health -= int(damage)
      elif (toPlayer.health > 0):
        self.callback.playerDead()
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

class ClientServer():
  PORT=7079
  #SERVER="192.168.1.116"
  SERVER="localhost"
