"""Test how the client handles messages from the server"""

import pytest
from msgHandler import ServerMsgHandler
from player import Player
from parameters import Parameters

# pylint:disable=redefined-outer-name


@pytest.fixture
def msg_handler(mocker):
    """Fixture for a message handler being tested"""
    game_logic = mocker.MagicMock()
    listening_thread = mocker.MagicMock()
    return ServerMsgHandler(listening_thread, game_logic)


def test_ping(msg_handler, mocker):
    """Test handling of PING message"""
    server = mocker.MagicMock()
    assert msg_handler.handleMsg("E(123def,1516565652,Ping())", server)
    server.queueMessage.assert_called_once_with("Pong(1516565652,1)")


def test_simple_pong(msg_handler, monkeypatch, mocker):
    """Test handling of PONG message which doesn't need a response"""
    server = mocker.MagicMock()
    monkeypatch.setattr('time.time', lambda: 300)
    mocker.patch("gameState.Timer", autospec=True)
    assert msg_handler.handleMsg("E(123def,1200,Pong(100,0))", server)
    server.setLatency.assert_called_once_with(100)
    server.setClientClockDrift.assert_called_once_with(1000)
    assert server.queueMessage.call_count == 0


def test_reply_pong(msg_handler, mocker):
    """Test handling of PONG message which requests a response"""
    server = mocker.MagicMock()
    assert msg_handler.handleMsg("E(123def,1516565852,Pong(1516565652,1))", server)
    server.queueMessage.assert_called_once_with("Pong(1516565852,0)")


def test_hello_new(msg_handler, mocker):
    """Test handling of HELLO message from new client"""
    server = mocker.MagicMock()
    msg_handler.listeningThread.isConnected.return_value = None
    msg_handler.gameLogic.gameState.createNewPlayer.return_value = Player(team_id=1, player_id=1)
    cgs = mocker.MagicMock()
    cgs.parameters = Parameters()
    msg_handler.gameLogic.gameState.withCurrGameState.side_effect = lambda x: x(cgs)
    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    msg_handler.listeningThread.recievedHello.assert_called_once_with(server, 0x123def)


def test_hello_existing(msg_handler, mocker):
    """Test handling of HELLO message from existing client"""
    server = mocker.MagicMock()
    msg_handler.listeningThread.isConnected.return_value = (3, 4)
    player = Player(team_id=3, player_id=4)
    msg_handler.gameLogic.gameState.getOrCreatePlayer.return_value = player
    cgs = mocker.MagicMock()
    cgs.parameters = Parameters()
    msg_handler.gameLogic.gameState.withCurrGameState.side_effect = lambda x: x(cgs)

    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    msg_handler.gameLogic.gameState.getOrCreatePlayer.assert_called_once_with(3, 4)
    server.queueMessage.assert_has_calls([
        mocker.call("PlayerSnapshot({\"playerID\": 4, \"gunDamage\": 1, \"teamID\": 3, \"health\": 5, \"ammo\": 100})"),
        mocker.call("ParametersSnapshot({\"parameters\": {\"player.maxHealth\": {\"effects\": [], \"baseValue\": 100}, \"gun.damage\": {\"effects\": [], \"baseValue\": 2}}})"),
        mocker.call("StartGame(1)")
    ])
    msg_handler.listeningThread.establishConnection.assert_called_once_with(server, player)


def test_hello_unstarted(msg_handler, mocker):
    """Test handling of HELLO message from new client when game is unstarted"""
    server = mocker.MagicMock()
    msg_handler.listeningThread.isConnected.return_value = None
    msg_handler.gameLogic.gameState.isGameStarted.return_value = False
    msg_handler.gameLogic.gameState.getOrCreatePlayer.return_value = Player(1, 1)
    cgs = mocker.MagicMock()
    cgs.parameters = Parameters()
    msg_handler.gameLogic.gameState.withCurrGameState.side_effect = lambda x: x(cgs)

    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    msg_handler.listeningThread.recievedHello.assert_called_once_with(server, 0x123def)


def test_recv_initialising_hit(msg_handler, mocker):
    """Test handling of hit message from initialising player"""
    server = mocker.MagicMock()
    server.clientTimeToServer.return_value = 200

    server2 = mocker.MagicMock()
    server2.clientTimeToServer.return_value = 200
    server2.clientId = 0x123def

    player = Player(team_id=1, player_id=1)

    msg_handler.listeningThread.initialisingConnection = server2
    msg_handler.gameLogic.gameState.createNewPlayer.return_value = player
    cgs = mocker.MagicMock()
    cgs.parameters = Parameters()
    msg_handler.gameLogic.gameState.withCurrGameState.side_effect = lambda x: x(cgs)

    assert msg_handler.handleMsg("E(456abc,100,Recv(2,2,InitHit))", server)

    msg_handler.gameLogic.hit.assert_has_calls([])  # This isn't a real hit, don't treat it as one
    msg_handler.gameLogic.gameState.createNewPlayer.assert_called_once()
    server2.queueMessage.assert_has_calls([
        mocker.call("PlayerSnapshot({\"playerID\": 1, \"gunDamage\": 1, \"teamID\": 1, \"health\": 5, \"ammo\": 100})"),
        mocker.call("ParametersSnapshot({\"parameters\": {\"player.maxHealth\": {\"effects\": [], \"baseValue\": 100}, \"gun.damage\": {\"effects\": [], \"baseValue\": 2}}})"),
        mocker.call("StartGame(1)")
    ])
    msg_handler.listeningThread.establishConnection.assert_called_once_with(server2, player)


def test_recv_initialising_hit_unstarted(msg_handler, mocker):
    """Test handling of hit message from initialising player when game is unstarted"""
    server = mocker.MagicMock()
    server.clientTimeToServer.return_value = 200

    server2 = mocker.MagicMock()
    server2.clientTimeToServer.return_value = 200
    server2.clientId = 0x123def

    player = Player(team_id=1, player_id=1)

    msg_handler.listeningThread.initialisingConnection = server2
    msg_handler.gameLogic.gameState.createNewPlayer.return_value = player
    msg_handler.gameLogic.gameState.isGameStarted.return_value = False
    cgs = mocker.MagicMock()
    cgs.parameters = Parameters()
    msg_handler.gameLogic.gameState.withCurrGameState.side_effect = lambda x: x(cgs)

    assert msg_handler.handleMsg("E(456abc,100,Recv(2,2,InitHit))", server)

    msg_handler.gameLogic.hit.assert_has_calls([])  # This isn't a real hit, don't treat it as one
    msg_handler.gameLogic.gameState.createNewPlayer.assert_called_once()
    server2.queueMessage.assert_has_calls([
        mocker.call("PlayerSnapshot({\"playerID\": 1, \"gunDamage\": 1, \"teamID\": 1, \"health\": 5, \"ammo\": 100})"),
        mocker.call("ParametersSnapshot({\"parameters\": {\"player.maxHealth\": {\"effects\": [], \"baseValue\": 100}, \"gun.damage\": {\"effects\": [], \"baseValue\": 2}}})"),
    ])
    msg_handler.listeningThread.establishConnection.assert_called_once_with(server2, player)


def test_recv_hit(msg_handler, mocker):
    """Test handling of normal hit message"""
    server = mocker.MagicMock()
    server.clientTimeToServer.return_value = 200

    assert msg_handler.handleMsg("E(123def,100,Recv(1,1,H2,1,3))", server)

    server.clientTimeToServer.assert_called_once_with(100)
    msg_handler.gameLogic.hit.assert_called_once_with(200, 1, 1, 2, 1, 3)


def test_recv_trigger(msg_handler, mocker):
    """Test handling of trigger message"""
    server = mocker.MagicMock()
    server.clientTimeToServer.return_value = 200

    assert msg_handler.handleMsg("E(123def,100,Recv(1,1,T))", server)

    server.clientTimeToServer.assert_called_once_with(100)
    msg_handler.gameLogic.trigger.assert_called_once_with(200, 1, 1)


def test_recv_triggerRelease(msg_handler, mocker):
    """Test handling of triggerRelease message"""
    server = mocker.MagicMock()
    server.clientTimeToServer.return_value = 200

    assert msg_handler.handleMsg("E(123def,100,Recv(1,1,t))", server)

    server.clientTimeToServer.assert_called_once_with(100)
    msg_handler.gameLogic.triggerRelease.assert_called_once_with(200, 1, 1)
