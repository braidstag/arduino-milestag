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

def test_ping(listening_thread, mocker):
    "Test handling of PING message"
    server = mocker.MagicMock()
    server2 = mocker.MagicMock()
    player = Player(1,1)
    clientId = 'abc123'

    listening_thread.unestablishedConnections = [server, server2]

    listening_thread.establishConnection(server, player, clientId)

    assert listening_thread.unestablishedConnections == [server2]
    assert listening_thread.connections[(1,1)] == server
    assert listening_thread.connectedClients[clientId] == (1,1)

#TODO lots more

