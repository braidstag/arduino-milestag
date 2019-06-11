"Test how the client handles messages from the server"

import pytest
from clientConnection import ClientConnection
from player import Player

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

def test_snapshot(client_connection, mocker, monkeypatch):
    "Test handling of SNAPSHOT message"
    monkeypatch.setattr('time.time', lambda:300)
    mocker.patch("gameState.Timer", autospec=True)
    assert client_connection.handleMsg('E(123def,1516565852,Snapshot({"playerID": 2, "maxHealth": 8, "teamID": 1, "health": 5, "gunDamage": 1, "ammo": 100, "maxAmmo": 100}))')

    p = Player(1, 2)
    p.maxHealth == 8
    p.health == 5
    p.gunDamage == 1
    p.ammo == 100
    p.maxAmmo == 100

    client_connection.game_logic.setSnapshot.assert_called_once_with(300, p)
