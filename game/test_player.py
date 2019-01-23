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
    jsonStr = '{"playerID": 2, "maxHealth": 8, "teamID": 1, "health": 5, "gunDamage": 1, "ammo": 100, "maxAmmo": 100}'
    p = json.loads(jsonStr, cls=Player.Decoder)

    assert p.playerID == 2
    assert p.teamID == 1
    assert p.maxHealth == 8
    assert p.health == 5
    assert p.gunDamage == 1
    assert p.ammo == 100
    assert p.maxAmmo == 100