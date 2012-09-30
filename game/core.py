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

class StandardGameLogic():
  def hit(self, toPlayer, fromTeam, fromPlayer, damage):
    if (fromPlayer == toPlayer.playerID and fromTeam == toPlayer.teamID):
      #self shot, ignore this
      pass
    else:
      toPlayer.health -= int(damage)

  def trigger(self, player):
    if player.ammo > 0:
      player.ammo = player.ammo - 1
      return True
    else:
      return False

class ClientServer():
  PORT=7079
  #SERVER="192.168.1.116"
  SERVER="localhost"
