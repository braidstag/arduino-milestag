#!/usr/bin/python

class Player():
  teamID = 0
  playerID = 0
  ammo = 100
  health = 5
  gunDamage = 1

  def __init__(self, teamID, playerID):
    self.teamID = int(teamID)
    self.playerID = int(playerID)

  def __str__(self):
    return "Player(team=%d, id=%d, ammo=%d, health=%d)" % (self.teamID, self.playerID, self.ammo, self.health)

class DefaultCallback():
  def playerDead(self):
    pass

class StandardGameLogic():
  def __init__(self, callback = DefaultCallback()):
    self.callback = callback

  def hit(self, toPlayer, fromTeam, fromPlayer, damage):
    if (fromPlayer == toPlayer.playerID and fromTeam == toPlayer.teamID):
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

  def trigger(self, player):
    if player.ammo > 0 and player.health > 0:
      player.ammo = player.ammo - 1
      return True
    else:
      return False

class ClientServer():
  PORT=7079
  #SERVER="192.168.1.116"
  SERVER="localhost"
