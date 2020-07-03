from __future__ import print_function

import json

class Stats(object):
    def __init__(self, copyFrom = None, shotsFired = 0, hitsReceived = 0, hitsGiven = 0, deaths = 0, kills = 0):
        if (copyFrom):
            shotsFired = shotsFired or copyFrom.shotsFired
            hitsReceived = hitsReceived or copyFrom.hitsReceived
            hitsGiven = hitsGiven or copyFrom.hitsGiven
            deaths = deaths or copyFrom.deaths
            kills = kills or copyFrom.kills

        object.__setattr__(self, "shotsFired", shotsFired)
        object.__setattr__(self, "hitsReceived", hitsReceived)
        object.__setattr__(self, "hitsGiven", hitsGiven)
        object.__setattr__(self, "deaths", deaths)
        object.__setattr__(self, "kills", kills)

    def __setattr__(self, *args):
        raise TypeError

    def __delattr__(self, *args):
        raise TypeError

    def __str__(self):
        return "Stats(%s)" % (str(self.__dict__), )

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def toSimpleTypes(self):
        return self.__dict__


class Player(object):

    def __init__(self, teamID = None, playerID = None, copyFrom = None, stats = None, ammo = None, health = None, gunDamage = None):
        if (copyFrom):
            teamID = teamID or copyFrom.teamID
            playerID = playerID or copyFrom.playerID
            if ammo == None:
                ammo = copyFrom.ammo
            if health == None:
                health = copyFrom.health
            if gunDamage == None:
                gunDamage = copyFrom.gunDamage

            if stats and not isinstance(stats, Stats):
                #This is an object literal which should be mixed in with the stats from copyFrom
                stats = Stats(copyFrom = copyFrom.stats, **stats)
            else:
                stats = stats or copyFrom.stats

        #Default values
        stats = stats or Stats()
        if ammo == None:
            ammo = 100
        if health == None:
            health = 5
        if gunDamage == None:
            gunDamage = 1

        #Type coercion
        teamID = int(teamID)
        playerID = int(playerID)

        object.__setattr__(self, "teamID", teamID)
        object.__setattr__(self, "playerID", playerID)
        object.__setattr__(self, "ammo", ammo)
        object.__setattr__(self, "health", health)
        object.__setattr__(self, "gunDamage", gunDamage)
        object.__setattr__(self, "stats", stats)

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
            return Player(copyFrom=self, health=self.health - int(damage))
        elif (self.health > 0):
            return Player(copyFrom=self, health=0)
        else:
            return self

#TODO: Should stats be included in here?
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
            return Player(
                teamID = jsonObj["teamID"],
                playerID = jsonObj["playerID"],
                ammo = jsonObj["ammo"],
                health = jsonObj["health"],
                gunDamage = jsonObj["gunDamage"]
            )