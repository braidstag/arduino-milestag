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

def test_addEvent_first(game_state, mocker):
    "Test handling of the first event"
    event = mocker.MagicMock()
    
    game_state.addEvent(event)
    
    event.apply.assert_called_once_with(game_state)
    assert game_state.uncertainEvents == [event]

def test_addEvent_latest(game_state, mocker):
    "Test handling of a subsequent, later event"
    event1 = GameEvent(100)
    event2 = GameEvent(200)
    mocker.spy(event2, 'apply')

    game_state.uncertainEvents = [event1]
    game_state.addEvent(event2)

    event2.apply.assert_called_once_with(game_state) # pylint:disable=E1101
    assert game_state.uncertainEvents == [event1, event2]

def test_addEvent_outOfOrder(game_state, mocker):
    "Test handling of a subsequent, earlier event"
    event1 = GameEvent(100)
    event2 = GameEvent(200)
    mocker.spy(event1, 'apply')
    mocker.spy(event2, 'apply')
    
    game_state.uncertainEvents = [event2]
    oldPlayers = game_state.players
    game_state.addEvent(event1)
    
    event1.apply.assert_called_once_with(game_state) # pylint:disable=E1101
    event2.apply.assert_called_once_with(game_state) # pylint:disable=E1101
    assert game_state.uncertainEvents == [event1, event2]
    assert id(oldPlayers) != id(game_state.players)

def test_adjustConfidencePoint_latest(game_state, mocker):
    "Test adjusting the confidence point to include all uncertain events"
    event1 = GameEvent(100)
    event2 = GameEvent(200)
    mocker.spy(event1, 'apply')
    mocker.spy(event2, 'apply')

    originalPlayers = {"dummyData"}
    game_state.players = originalPlayers
    game_state.uncertainEvents = [event1, event2]
    game_state.adjustConfidencePoint(300)

    #assert we just baseline onto the latest without re-applying.
    assert event1.apply.call_count == 0 # pylint:disable=E1101
    assert event2.apply.call_count == 0 # pylint:disable=E1101
    assert game_state.uncertainEvents == []
    assert originalPlayers == game_state.baselinePlayers

def test_adjustConfidencePoint_earliest(game_state, mocker):
    "Test adjusting the confidence point to include no uncertain events"
    event1 = GameEvent(100)
    event2 = GameEvent(200)
    mocker.spy(event1, 'apply')
    mocker.spy(event2, 'apply')

    game_state.uncertainEvents = [event1, event2]
    game_state.adjustConfidencePoint(50)

    #assert we don't do anything.
    assert event1.apply.call_count == 0 # pylint:disable=E1101
    assert event2.apply.call_count == 0 # pylint:disable=E1101
    assert game_state.uncertainEvents == [event1, event2]

def test_adjustConfidencePoint_middle(game_state, mocker):
    "Test adjusting the confidence point to include some, but not all, uncertain events"
    event1 = GameEvent(100)
    event2 = GameEvent(200)
    mocker.spy(event1, 'apply')
    mocker.spy(event2, 'apply')

    game_state.uncertainEvents = [event1, event2]
    game_state.adjustConfidencePoint(150)

    assert event1.apply.call_count == 1 # This is re-applied to find the new baseline  # pylint:disable=E1101
    assert event2.apply.call_count == 0 # We don't need to re-apply this though  # pylint:disable=E1101
    assert game_state.uncertainEvents == [event2]
