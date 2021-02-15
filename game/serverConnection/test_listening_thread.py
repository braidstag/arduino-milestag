"Test listening for new connections and keeping track of them"

import pytest
from listeningThread import ListeningThread
from player import Player

# pylint:disable=redefined-outer-name

@pytest.fixture
def listening_thread(mocker, monkeypatch):
    "Fixture for a message handler being tested"
    monkeypatch.setattr('socket.socket', mocker.MagicMock())
    #    mocker.patch(ListeningThread, 'socket.socket')
    game_logic = mocker.MagicMock()
    listeningThread = ListeningThread(game_logic)
    mocker.spy(listeningThread, 'msgHandler')
    return listeningThread

def test_establishConnection(listening_thread, mocker):
    "Test establishConnection"
    server = mocker.MagicMock()
    server2 = mocker.MagicMock()
    player = Player(teamID = 1, playerID = 1)
    clientId = 'abc123'
    server.clientId = clientId

    listening_thread.uninitialisedConnections = set([server, server2])

    listening_thread.establishConnection(server, player)

    assert listening_thread.uninitialisedConnections == set([server2])
    assert listening_thread.initialisingConnection == None
    assert listening_thread.connections[(1,1)] == server
    assert listening_thread.connectedClients[clientId] == (1,1)
    listening_thread.gameLogic.gameState._notifyPlayerInitialisedListeners.assert_called_once()

def test_establishConnection_initialising(listening_thread, mocker):
    "Test establishConnection for an initialising connection"
    server = mocker.MagicMock()
    server2 = mocker.MagicMock()
    player = Player(teamID = 1, playerID = 1)
    clientId = 'abc123'
    server.clientId = clientId

    listening_thread.uninitialisedConnections = set([server2])
    listening_thread.initialisingConnection = server

    listening_thread.establishConnection(server, player)

    assert listening_thread.uninitialisedConnections == set([server2])
    assert listening_thread.initialisingConnection == None
    assert listening_thread.connections[(1,1)] == server
    assert listening_thread.connectedClients[clientId] == (1,1)
    listening_thread.gameLogic.gameState._notifyPlayerInitialisedListeners.assert_called_once()

def test_startInitialising(listening_thread, mocker):
    "Test startInitialising"
    server = mocker.MagicMock()

    listening_thread.uninitialisedConnections = set([server])

    listening_thread.startInitialising(server)

    assert listening_thread.initialisingConnection == server
    assert listening_thread.uninitialisedConnections == set([])

    listening_thread.gameLogic.gameState._notifyPlayerInitialisingListeners.assert_called_once()



#TODO lots more

