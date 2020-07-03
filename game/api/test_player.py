# pylint:disable=redefined-outer-name
import pytest
import time
from falcon import HTTPBadRequest, testing

from restapi import create_api
from player import Player
from parameters import Parameters

@pytest.fixture()
def current_game_state(mocker):
    cgs = mocker.MagicMock()
    cgs.parameters = Parameters()

    return cgs

@pytest.fixture()
def game_state(mocker, current_game_state):
    gameState = mocker.MagicMock()
    gameState.withCurrGameState.side_effect = lambda x: x(current_game_state)

    return gameState

@pytest.fixture()
def game_logic(mocker):
    return mocker.MagicMock()

@pytest.fixture()
def client(game_state, game_logic):
    return testing.TestClient(create_api(game_state, game_logic))

def test_getListSummary(game_state, game_logic, current_game_state, client, monkeypatch, mocker):
    player1 = Player(1, 1)
    player1.ammo = 95
    player1.health = 8

    player2 = Player(2, 1)
    player2.ammo = 100
    player2.health = 7

    current_game_state.players = {
        (1,1): player1,
        (2,1): player2
    }
    current_game_state.gameTime = 1200

    result = client.simulate_get('/players')

    assert result.json == {
        u'players': [
            {
                'teamId': 1,
                'playerId': 1,
                'ammo': 95,
                'health': 8,
            },
            {
                'teamId': 2,
                'playerId': 1,
                'ammo': 100,
                'health': 7,
            }
        ]
    }

    assert result.status_code == 200

def test_getListFull(game_state, game_logic, current_game_state, client, monkeypatch, mocker):
    player1 = Player(teamID = 1, playerID = 1, ammo = 95, health = 8)
    player2 = Player(teamID = 2, playerID = 1, ammo = 100, health = 7)

    current_game_state.players = {
        (1,1): player1,
        (2,1): player2
    }
    current_game_state.gameTime = 1200

    result = client.simulate_get('/players?fullInfo=True')

    assert result.json == {
        u'players': [
            {
                u'teamId': 1,
                u'playerId': 1,
                u'ammo': 95,
                u'health': 8,
                u'parameters': {
                    u'gun.damage': {
                        u'baseValue': 2,
                        u'currentValue': 2,
                        u'effects': []
                    },
                    u'player.maxHealth': {
                        u'baseValue': 100,
                        u'currentValue': 100,
                        u'effects': []
                    }
                },
                u'stats': {
                    u'deaths': 0,
                    u'hitsGiven': 0,
                    u'hitsReceived': 0,
                    u'kills': 0,
                    u'shotsFired': 0
                }
            },
            {
                u'teamId': 2,
                u'playerId': 1,
                u'ammo': 100,
                u'health': 7,
                u'parameters': {
                    u'gun.damage': {
                        u'baseValue': 2,
                        u'currentValue': 2,
                        u'effects': []
                    },
                    u'player.maxHealth': {
                        u'baseValue': 100,
                        u'currentValue': 100,
                        u'effects': []
                    }
                },
                u'stats': {
                    u'deaths': 0,
                    u'hitsGiven': 0,
                    u'hitsReceived': 0,
                    u'kills': 0,
                    u'shotsFired': 0
                }
            }
        ]
    }

    assert result.status_code == 200

def test_getDetails(game_state, game_logic, current_game_state, client, monkeypatch, mocker):
    player1 = Player(teamID = 1, playerID = 1, ammo = 95, health = 8)
    player2 = Player(teamID = 2, playerID = 1, ammo = 100, health = 7)

    current_game_state.players = {
        (1,1): player1,
        (2,1): player2
    }
    current_game_state.gameTime = 1200

    result = client.simulate_get('/players/2/1')

    assert result.json == {
        u'teamId': 2,
        u'playerId': 1,
        u'ammo': 100,
        u'health': 7,
        u'parameters': {
            u'gun.damage': {
                u'baseValue': 2,
                u'currentValue': 2,
                u'effects': []
            },
            u'player.maxHealth': {
                u'baseValue': 100,
                u'currentValue': 100,
                u'effects': []
            }
        },
        u'stats': {
            u'deaths': 0,
            u'hitsGiven': 0,
            u'hitsReceived': 0,
            u'kills': 0,
            u'shotsFired': 0
        }
    }

    assert result.status_code == 200
