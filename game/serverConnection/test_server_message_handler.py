"Test how the client handles messages from the server"

import pytest
from msgHandler import ServerMsgHandler
from player import Player

# pylint:disable=redefined-outer-name

@pytest.fixture
def msg_handler(mocker):
    "Fixture for a message handler being tested"
    game_logic = mocker.MagicMock()
    listening_thread = mocker.MagicMock()
    return ServerMsgHandler(listening_thread, game_logic)

def test_ping(msg_handler, mocker):
    "Test handling of PING message"
    server = mocker.MagicMock()
    assert msg_handler.handleMsg("E(123def,1516565652,Ping())", server)
    server.queueMessage.assert_called_once_with("Pong(1516565652,1)")

def test_simple_pong(msg_handler, monkeypatch, mocker):
    "Test handling of PONG message which doesn't need a response"
    server = mocker.MagicMock()
    monkeypatch.setattr('time.time', lambda:300)
    mocker.patch("gameState.Timer", autospec=True)
    assert msg_handler.handleMsg("E(123def,1200,Pong(100,0))", server)
    server.setLatency.assert_called_once_with(100)
    server.setClientClockDrift.assert_called_once_with(1000)
    assert server.queueMessage.call_count == 0

def test_reply_pong(msg_handler, mocker):
    "Test handling of PONG message which requests a response"
    server = mocker.MagicMock()
    assert msg_handler.handleMsg("E(123def,1516565852,Pong(1516565652,1))", server)
    server.queueMessage.assert_called_once_with("Pong(1516565852,0)")

def test_hello_new(msg_handler, mocker):
    "Test handling of HELLO message from new client"
    server = mocker.MagicMock()
    msg_handler.listeningThread.isConnected.return_value = None
    msg_handler.gameLogic.gameState.createNewPlayer.return_value = Player(1, 1)
    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    msg_handler.gameLogic.gameState.createNewPlayer.assert_called_once_with()
    server.queueMessage.assert_has_calls([
        mocker.call("Snapshot({\"playerID\": 1, \"maxHealth\": 8, \"teamID\": 1, \"health\": 5, \"gunDamage\": 1, \"ammo\": 100, \"maxAmmo\": 100})"),
        mocker.call("StartGame(1)")
    ])

def test_hello_existing(msg_handler, mocker):
    "Test handling of HELLO message from existing client"
    server = mocker.MagicMock()
    msg_handler.listeningThread.isConnected.return_value = (3, 4)
    msg_handler.gameLogic.gameState.getOrCreatePlayer.return_value = Player(3, 4)

    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    msg_handler.gameLogic.gameState.getOrCreatePlayer.assert_called_once_with(3, 4)
    server.queueMessage.assert_has_calls([
        mocker.call("Snapshot({\"playerID\": 4, \"maxHealth\": 8, \"teamID\": 3, \"health\": 5, \"gunDamage\": 1, \"ammo\": 100, \"maxAmmo\": 100})"),
        mocker.call("StartGame(1)")
    ])

def test_hello_unstarted(msg_handler, mocker):
    "Test handling of HELLO message from new client"
    server = mocker.MagicMock()
    msg_handler.gameLogic.gameState.isGameStarted.return_value = False
    msg_handler.gameLogic.gameState.getOrCreatePlayer.return_value = Player(1, 1)

    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    server.queueMessage.assert_called_once_with("Snapshot({\"playerID\": 1, \"maxHealth\": 8, \"teamID\": 1, \"health\": 5, \"gunDamage\": 1, \"ammo\": 100, \"maxAmmo\": 100})")

def test_recv_hit(msg_handler, mocker):
    "Test handling of HELLO message from new client"
    server = mocker.MagicMock()
    server.clientTimeToServer.return_value = 200

    assert msg_handler.handleMsg("E(123def,100,Recv(1,1,H2,1,3))", server)

    server.clientTimeToServer.assert_called_once_with(100)
    msg_handler.gameLogic.hit.assert_called_once_with(200, 1, 1, 2, 1, 3)

def test_recv_trigger(msg_handler, mocker):
    "Test handling of HELLO message from new client"
    server = mocker.MagicMock()
    server.clientTimeToServer.return_value = 200

    assert msg_handler.handleMsg("E(123def,100,Recv(1,1,T))", server)

    server.clientTimeToServer.assert_called_once_with(100)
    msg_handler.gameLogic.trigger.assert_called_once_with(200, 1, 1)

def test_recv_triggerRelease(msg_handler, mocker):
    "Test handling of HELLO message from new client"
    server = mocker.MagicMock()
    server.clientTimeToServer.return_value = 200

    assert msg_handler.handleMsg("E(123def,100,Recv(1,1,t))", server)

    server.clientTimeToServer.assert_called_once_with(100)
    msg_handler.gameLogic.triggerRelease.assert_called_once_with(200, 1, 1)