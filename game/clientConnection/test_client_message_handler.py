"Test how the client handles messages from the server"

import pytest
from clientConnection import ClientConnection
from player import Player
from parameters import Parameters

# pylint:disable=redefined-outer-name

@pytest.fixture
def client_connection(mocker, monkeypatch):
    "Fixture for a client connection being tested"
    monkeypatch.setattr('socket.socket', mocker.MagicMock())
    game_logic = mocker.MagicMock()
    main = mocker.MagicMock()
    cc = ClientConnection(main, game_logic)
    cc.queueMessage = mocker.MagicMock()
    return cc

def test_ping(client_connection, mocker):
    "Test handling of PING message"
    assert client_connection.handleMsg("E(123def,1516565652,Ping())")
    client_connection.queueMessage.assert_called_once_with("Pong(1516565652,0)")

def test_simple_pong(client_connection, monkeypatch, mocker):
    "Test handling of PONG message which doesn't need a response"
    assert client_connection.handleMsg("E(123def,1200,Pong(100,0))")
    assert client_connection.queueMessage.call_count == 0

def test_reply_pong(client_connection, mocker):
    "Test handling of PONG message which requests a response"
    assert client_connection.handleMsg("E(123def,1516565852,Pong(1516565652,1))")
    client_connection.queueMessage.assert_called_once_with("Pong(1516565852,0)")

def test_playerSnapshot(client_connection, mocker, monkeypatch):
    "Test handling of PLAYER_SNAPSHOT message"
    monkeypatch.setattr('time.time', lambda:300)
    mocker.patch("gameState.Timer", autospec=True)
    assert client_connection.handleMsg('E(123def,1516565852,PlayerSnapshot({"playerID": 2, "teamID": 1, "health": 5, "gunDamage": 1, "ammo": 100}))')

    p = Player(1, 2)
    p.health == 5
    p.gunDamage == 1
    p.ammo == 100

    client_connection.game_logic.setPlayerSnapshot.assert_called_once_with(300, p)

def test_parametersSnapshot(client_connection, mocker, monkeypatch):
    "Test handling of PARAMETERS_SNAPSHOT message"
    monkeypatch.setattr('time.time', lambda:300)
    mocker.patch("gameState.Timer", autospec=True)
    assert client_connection.handleMsg('E(123def,1516565852,ParametersSnapshot({"parameters": {"player.maxHealth": {"effects": [], "baseValue": 100}, "gun.damage": {"effects": [], "baseValue": 2}}}))')

    client_connection.game_logic.setParametersSnapshot.assert_called_once_with(300, Parameters())

def test_startInitialising(client_connection, mocker, monkeypatch):
    "Test handling of START_INITIALISING message"
    monkeypatch.setattr('time.time', lambda:300)
    mocker.patch("gameState.Timer", autospec=True)
    assert client_connection.handleMsg('E(123def,1516565852,StartInitialising())')

    client_connection.game_logic.gameState.startInitialisation.assert_called_once()
