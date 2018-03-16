"Test how the client handles messages from the server"

import pytest
from server import ServerGameState
from gameEvents import GameEvent, HitEvent

# pylint:disable=redefined-outer-name

@pytest.fixture
def game_state(mocker):
    "Fixture for a message handler being tested"
    listening_thread = mocker.MagicMock()
    game_state = ServerGameState()
    game_state.setListeningThread(listening_thread)
    return game_state

def test_addHitEvent_outOfOrder(game_state, mocker):
    "Test handling of a subsequent, earlier event "
    event1 = HitEvent(100, 1, 1, 2, 1, 999)
    event2 = HitEvent(200, 2, 1, 1, 1, 999)

    game_state.getOrCreatePlayer(1, 1)
    game_state.getOrCreatePlayer(2, 1)
    game_state.startGame()

    game_state.addEvent(event2)
    
    assert game_state.players[(1, 1)].health > 0
    assert game_state.players[(2, 1)].health == 0

    game_state.addEvent(event1)
    
    assert game_state.players[(1, 1)].health == 0
    assert game_state.players[(2, 1)].health > 0

