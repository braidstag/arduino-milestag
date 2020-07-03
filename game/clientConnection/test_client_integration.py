"Test how the client handles messages from the server"

import pytest
from gameLogic import GameLogic
from gameState import GameState
from clientConnection import ClientConnection

# pylint:disable=redefined-outer-name

@pytest.fixture
def game_state():
    return GameState(isClient=True)

@pytest.fixture
def game_logic(game_state):
    return GameLogic(game_state)

@pytest.fixture
def client_connection(mocker, monkeypatch, game_logic):
    "Fixture for a client connection being tested"
    #monkeypatch.setattr('socket.socket', mocker.MagicMock())
    monkeypatch.setattr('clientConnection.clientConnection.ClientConnection._openConnection', mocker.MagicMock())
    #TODO: mock serial and use a real Client instance
    main = mocker.MagicMock()
    cc = ClientConnection(main, game_logic)
    cc.queueMessage = mocker.MagicMock()
    return cc

def test_snapshot(client_connection, game_logic, game_state, mocker):
    "Test handling of snapshot message from server after receiving a shot we shouldn't have received"
    game_logic.setMainPlayer(60, game_state.getOrCreatePlayer(1, 1))
    game_logic.startGame(50)

    #check that initial player is as expected.
    p = game_state.getMainPlayer()
    assert p.health == 5

    #get shot
    #TODO: when we have a real client, mock serial to send this Hit from the gun itself.
    game_logic.hit(100, None, None, 2, 3, 1)

    #assert that we noticed that Hit
    p = game_state.getMainPlayer()
    assert p.health == 4

    #Get sent an snapshot from the server. We weren't hit after all :-)
    client_connection.handleMsg('E(123def,200,PlayerSnapshot({"playerID": 2, "teamID": 1, "health": 5, "gunDamage": 1, "ammo": 100}))')

    #assert that we used the snapshot and reverted the Hit.
    p = game_state.getMainPlayer()
    assert p.health == 5
