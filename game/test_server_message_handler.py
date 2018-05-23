"Test how the client handles messages from the server"

import pytest
from server import ServerMsgHandler

# pylint:disable=redefined-outer-name

@pytest.fixture
def msg_handler(mocker):
    "Fixture for a message handler being tested"
    game_state = mocker.MagicMock()
    listening_thread = mocker.MagicMock()
    return ServerMsgHandler(listening_thread, game_state)

def test_ping(msg_handler, mocker):
    "Test handling of PING message"
    server = mocker.MagicMock()
    assert msg_handler.handleMsg("E(123def,1516565652,Ping())", server)
    server.queueMessage.assert_called_once_with("Pong(1516565652,1)")

def test_simple_pong(msg_handler, mocker):
    "Test handling of PONG message which doesn't need a response"
    server = mocker.MagicMock()
    server.timeProvider.return_value = 300
    assert msg_handler.handleMsg("E(123def,1200,Pong(100,0))", server)
    server.setLatency.assert_called_once_with(100)
    server.setClientClockDrift.assert_called_once_with(1000)

def test_reply_pong(msg_handler, mocker):
    "Test handling of PONG message which requests a response"
    server = mocker.MagicMock()
    assert msg_handler.handleMsg("E(123def,1516565852,Pong(1516565652,1))", server)
    server.queueMessage.assert_called_once_with("Pong(1516565852,0)")

def test_hello_new(msg_handler, mocker):
    "Test handling of HELLO message from new client"
    server = mocker.MagicMock()
    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    server.queueMessage.assert_has_calls([
        mocker.call("TeamPlayer(1,1)"),
        mocker.call("StartGame(1)")
    ])

def test_hello_existing(msg_handler, mocker):
    "Test handling of HELLO message from existing client"
    server = mocker.MagicMock()
    msg_handler.listeningThread.isConnected.return_value = (3, 4)
    msg_handler.gameState.getOrCreatePlayer().teamID = 3
    msg_handler.gameState.getOrCreatePlayer().playerID = 4
    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    server.queueMessage.assert_has_calls([
        mocker.call("TeamPlayer(3,4)"),
        mocker.call("StartGame(1)")
    ])

def test_hello_unstarted(msg_handler, mocker):
    "Test handling of HELLO message from new client"
    server = mocker.MagicMock()
    msg_handler.gameState.isGameStarted.return_value = False
    assert msg_handler.handleMsg("E(123def,1516565852,Hello())", server)
    server.queueMessage.assert_called_once_with("TeamPlayer(1,1)")
