"""Test listening for new connections and keeping track of them"""

import pytest
from listeningThread import ListeningThread
from player import Player

# pylint:disable=redefined-outer-name


@pytest.fixture
def listening_thread(mocker, monkeypatch):
    """Fixture for a message handler being tested"""
    monkeypatch.setattr('socket.socket', mocker.MagicMock())
    #    mocker.patch(ListeningThread, 'socket.socket')
    game_logic = mocker.MagicMock()
    listening_thread = ListeningThread(game_logic)
    mocker.spy(listening_thread, 'msgHandler')
    return listening_thread


def test_establishConnection(listening_thread, mocker):
    """Test establishConnection"""
    server = mocker.MagicMock()
    server2 = mocker.MagicMock()
    player = Player(team_id=1, player_id=1)
    client_id = 'abc123'
    server.clientId = client_id

    listening_thread.uninitialisedConnections = {server, server2}

    listening_thread.establishConnection(server, player)

    assert listening_thread.uninitialisedConnections == {server2}
    assert listening_thread.initialisingConnection is None
    assert listening_thread.connections[(1, 1)] == server
    assert listening_thread.connectedClients[client_id] == (1, 1)
    listening_thread.gameLogic.gameState._notifyPlayerInitialisedListeners.assert_called_once()


def test_establishConnection_initialising(listening_thread, mocker):
    """Test establishConnection for an initialising connection"""
    server = mocker.MagicMock()
    server2 = mocker.MagicMock()
    player = Player(team_id=1, player_id=1)
    client_id = 'abc123'
    server.clientId = client_id

    listening_thread.uninitialisedConnections = {server2}
    listening_thread.initialisingConnection = server

    listening_thread.establishConnection(server, player)

    assert listening_thread.uninitialisedConnections == {server2}
    assert listening_thread.initialisingConnection is None
    assert listening_thread.connections[(1, 1)] == server
    assert listening_thread.connectedClients[client_id] == (1, 1)
    listening_thread.gameLogic.gameState._notifyPlayerInitialisedListeners.assert_called_once()


def test_startInitialising(listening_thread, mocker):
    """Test startInitialising"""
    server = mocker.MagicMock()

    listening_thread.uninitialisedConnections = {server}

    listening_thread.startInitialising(server)

    assert listening_thread.initialisingConnection == server
    assert listening_thread.uninitialisedConnections == set([])

    listening_thread.gameLogic.gameState._notifyPlayerInitialisingListeners.assert_called_once()

# TODO lots more
