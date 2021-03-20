# pylint:disable=redefined-outer-name
from __future__ import print_function

import json

from player import Player


def test_serialising():
    p = Player(1, 2)

    jsonStr = json.dumps(p, cls=Player.Encoder)
    jsonObj = json.loads(jsonStr)

    assert jsonObj["playerID"] == 2
    assert jsonObj["teamID"] == 1
    assert jsonObj["health"] == p.health


def test_deserialising():
    jsonStr = '{"playerID": 2, "teamID": 1, "health": 5, "gunDamage": 1, "ammo": 100}'
    p = json.loads(jsonStr, cls=Player.Decoder)

    assert p.player_id == 2
    assert p.team_id == 1
    assert p.health == 5
    assert p.gun_damage == 1
    assert p.ammo == 100


def test_copy_from():
    p1 = Player(team_id=1, player_id=2, health=5)
    p2 = Player(copy_from=p1, health=10)

    assert p2.health == 10

    p3 = Player(copy_from=p1, health=0)

    assert p3.health == 0
