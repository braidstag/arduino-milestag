from __future__ import print_function


class Player():

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

    def __repr__(self):
        return "Player(team=%d, id=%d, ammo=%d, health=%d)" % (self.teamID, self.playerID, self.ammo, self.health)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def reduceHealth(self, damage):
        if (self.health > int(damage)):
            self.health -= int(damage)
        elif (self.health > 0):
            self.health = 0
        else:
            # already have 0 health
            pass
