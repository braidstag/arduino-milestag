from __future__ import print_function

import json


class Stats(object):
    def __init__(self, copy_from=None, shots_fired=0, hits_received=0, hits_given=0, deaths=0, kills=0):
        if copy_from:
            shots_fired = shots_fired or copy_from.shots_fired
            hits_received = hits_received or copy_from.hits_received
            hits_given = hits_given or copy_from.hits_given
            deaths = deaths or copy_from.deaths
            kills = kills or copy_from.kills

        object.__setattr__(self, "shots_fired", shots_fired)
        object.__setattr__(self, "hits_received", hits_received)
        object.__setattr__(self, "hits_given", hits_given)
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

    team_id = None
    player_id = None
    stats = None
    ammo = None
    health = None
    gun_damage = None

    def __init__(self, team_id=None, player_id=None, copy_from=None, stats=None, ammo=None, health=None, gun_damage=None):
        if copy_from:
            team_id = team_id or copy_from.team_id
            player_id = player_id or copy_from.player_id
            if ammo is None:
                ammo = copy_from.ammo
            if health is None:
                health = copy_from.health
            if gun_damage is None:
                gun_damage = copy_from.gun_damage

            if stats and not isinstance(stats, Stats):
                # This is an object literal which should be mixed in with the stats from copyFrom
                stats = Stats(copy_from=copy_from.stats, **stats)
            else:
                stats = stats or copy_from.stats

        # Default values
        stats = stats or Stats()
        if ammo is None:
            ammo = 100
        if health is None:
            health = 5
        if gun_damage is None:
            gun_damage = 1

        # Type coercion
        team_id = int(team_id)
        player_id = int(player_id)

        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "player_id", player_id)
        object.__setattr__(self, "ammo", ammo)
        object.__setattr__(self, "health", health)
        object.__setattr__(self, "gun_damage", gun_damage)
        object.__setattr__(self, "stats", stats)

    def __str__(self):
        return "Player(team=%d, id=%d, ammo=%d, health=%d)" % (self.team_id, self.player_id, self.ammo, self.health)

    def __repr__(self):
        return "Player(team=%d, id=%d, ammo=%d, health=%d)" % (self.team_id, self.player_id, self.ammo, self.health)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def reduceHealth(self, damage):
        if self.health > int(damage):
            return Player(copy_from=self, health=self.health - int(damage))
        elif self.health > 0:
            return Player(copy_from=self, health=0)
        else:
            return self

# TODO: Should stats be included in here?
    class Encoder(json.JSONEncoder):
        def default(self, obj):  # https://github.com/PyCQA/pylint/issues/414 pylint: disable=E0202
            """encode as JSON"""
            return {
                'teamID': obj.team_id,
                'playerID': obj.player_id,
                'ammo': obj.ammo,
                'health': obj.health,
                'gunDamage': obj.gun_damage,
            }

    class Decoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            super(Player.Decoder, self).__init__(object_hook=self.dict_to_object, *args, **kwargs)

        @staticmethod
        def dict_to_object(json_obj):
            """decode JSON"""
            return Player(
                team_id=json_obj["teamID"],
                player_id=json_obj["playerID"],
                ammo=json_obj["ammo"],
                health=json_obj["health"],
                gun_damage=json_obj["gunDamage"]
            )
