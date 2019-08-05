from __future__ import print_function

import json

class Player():

    def __init__(self, teamID, playerID):
        self.teamID = int(teamID)
        self.playerID = int(playerID)
        self.reset()

    def reset(self):
        self.ammo = 100
        self.health = 5
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

    class Encoder(json.JSONEncoder):
        def default(self, obj): # https://github.com/PyCQA/pylint/issues/414 pylint: disable=E0202
            """encode as JSON"""
            return {
                'teamID': obj.teamID,
                'playerID': obj.playerID,
                'ammo': obj.ammo,
                'health': obj.health,
                'gunDamage': obj.gunDamage,
            }

    class Decoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            super(Player.Decoder, self).__init__(object_hook=self.dict_to_object, *args, **kwargs)

        def dict_to_object(self, jsonObj):
            """decode JSON"""
            p = Player(jsonObj["teamID"], jsonObj["playerID"])
            p.ammo = jsonObj["ammo"]
            p.health = jsonObj["health"]
            p.gunDamage = jsonObj["gunDamage"]

            return p