# pylint:disable=redefined-outer-name,E1101
import pytest
import time
from mock import call, ANY

from gameState import GameState
from player import Player
from gameEvents import GameEvent

import gameState

@pytest.fixture
def game_state():
    gameState = GameState()
    return gameState

def test_add_event_before_confidence_point(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    mocker.spy(event, "apply")
    game_state.confidencePoint = 60

    with pytest.raises(RuntimeError):
        game_state.addEvent(event)

    assert event.apply.call_count == 0
    assert game_state.uncertainEvents == []

def test_add_past_event(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    mocker.spy(event, "apply")

    game_state.addEvent(event)

    assert event.apply.call_count == 1
    assert game_state.uncertainEvents == [event]

def test_add_2_past_events_in_order(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    mocker.spy(event, "apply")
    event2 = GameEvent(60)
    mocker.spy(event2, "apply")

    game_state.addEvent(event)
    game_state.addEvent(event2)

    assert event.apply.call_count == 1
    assert event2.apply.call_count == 1
    assert game_state.uncertainEvents == [event, event2]

def test_add_3_past_events_out_of_order(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    mocker.spy(event, "apply")
    event2 = GameEvent(60)
    mocker.spy(event2, "apply")
    event3 = GameEvent(70)
    mocker.spy(event3, "apply")

    game_state.addEvent(event3)
    game_state.addEvent(event)
    game_state.addEvent(event2)

    #Once when added, once when re-playing after each event is added.
    assert event3.apply.call_count == 3
    assert event.apply.call_count == 2
    assert event2.apply.call_count == 1
    assert game_state.uncertainEvents == [event, event2, event3]

def test_add_events_reentrant_past_in_order(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    event2 = GameEvent(60)
    event3 = GameEvent(70)
    mocker.spy(event, "apply")
    mocker.patch.object(event2, 'apply', autospec=True, side_effect=[event3, None])
    mocker.spy(event3, "apply")

    game_state.addEvent(event)
    game_state.addEvent(event2)

    assert event.apply.call_count == 1
    assert event2.apply.call_count == 1
    assert event3.apply.call_count == 1
    assert game_state.uncertainEvents == [event, event2, event3]
    assert game_state.futureEvents == []

def test_add_past_events_reentrant_past_out_of_order(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    event2 = GameEvent(60)
    event3 = GameEvent(70)
    mocker.patch.object(event, 'apply', autospec=True, side_effect=[event2, None])
    mocker.spy(event2, "apply")
    mocker.spy(event3, "apply")

    game_state.addEvent(event3)
    game_state.addEvent(event)

    #Once when added, once when re-playing after each event is added.
    assert event3.apply.call_count == 3
    assert event.apply.call_count == 2
    assert event2.apply.call_count == 1
    assert game_state.uncertainEvents == [event, event2, event3]
    assert game_state.futureEvents == []

def test_add_events_reentrant_future(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    event2 = GameEvent(60)
    event3 = GameEvent(170)
    mocker.patch.object(event, 'apply', autospec=True, side_effect=[event3, None])
    mocker.spy(event2, "apply")
    mocker.spy(event3, "apply")

    game_state.addEvent(event2)
    game_state.addEvent(event)

    #Once when added, once when re-playing after each event is added.
    assert event2.apply.call_count == 2
    assert event.apply.call_count == 1
    assert event3.apply.call_count == 0
    assert game_state.uncertainEvents == [event, event2]
    assert game_state.futureEvents == [event3]

def test_add_future_event(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(150)
    mocker.spy(event, "apply")

    game_state.addEvent(event)

    gameState.Timer.assert_called_once_with(50, ANY)

    assert event.apply.call_count == 0
    assert game_state.futureEvents == [event]

def test_add_2_future_events_in_order(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(150)
    mocker.spy(event, "apply")
    event2 = GameEvent(160)
    mocker.spy(event2, "apply")

    game_state.addEvent(event)
    game_state.addEvent(event2)

    assert gameState.Timer.call_args_list == [call(50, ANY), call(50, ANY)]
    assert gameState.Timer.return_value.cancel.call_count == 1
    assert event.apply.call_count == 0
    assert event2.apply.call_count == 0
    assert game_state.futureEvents == [event, event2]

def test_add_2_future_events_out_of_order(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(150)
    mocker.spy(event, "apply")
    event2 = GameEvent(160)
    mocker.spy(event2, "apply")

    game_state.addEvent(event2)
    game_state.addEvent(event)

    assert gameState.Timer.call_args_list == [call(60, ANY), call(50, ANY)]
    assert gameState.Timer.return_value.cancel.call_count == 1
    assert event.apply.call_count == 0
    assert event2.apply.call_count == 0
    assert game_state.futureEvents == [event2, event]

def test_add_future_event_recheck_after_due(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(150)
    mocker.spy(event, "apply")

    #Add the future event
    game_state.addEvent(event)

    gameState.Timer.assert_called_once_with(50, ANY)
    assert event.apply.call_count == 0
    assert game_state.uncertainEvents == []
    assert game_state.futureEvents == [event]

    #Jump forward in time (and reset timer mock)
    gameState.Timer.reset_mock()
    monkeypatch.setattr('time.time', lambda: 200)

    #Check the now overdue event
    game_state._recheckTimer()

    assert gameState.Timer.return_value.cancel.call_count == 1
    assert gameState.Timer.call_count == 0
    assert event.apply.call_count == 1
    assert game_state.uncertainEvents == [event]
    assert game_state.futureEvents == []

def test_handle_future_event_timer_with_only_event(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(150)
    mocker.spy(event, "apply")

    #Add the future event
    game_state.addEvent(event)

    gameState.Timer.assert_called_once_with(50, ANY)
    assert event.apply.call_count == 0
    assert game_state.uncertainEvents == []
    assert game_state.futureEvents == [event]

    #Jump forward in time (and reset timer mock)
    timerHandler = gameState.Timer.call_args[0][1]
    gameState.Timer.reset_mock()
    monkeypatch.setattr('time.time', lambda: 200)

    #call the timer handler
    timerHandler()

    assert gameState.Timer.return_value.cancel.call_count == 0
    assert gameState.Timer.call_count == 0
    assert event.apply.call_count == 1
    assert game_state.uncertainEvents == [event]
    assert game_state.futureEvents == []

def test_handle_future_event_timer_with_first_event(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(150)
    mocker.spy(event, "apply")

    event2 = GameEvent(250)
    mocker.spy(event2, "apply")

    #Add the future event
    game_state.addEvent(event)
    game_state.addEvent(event2)

    assert gameState.Timer.call_args_list == [call(50, ANY), call(50, ANY)]
    assert event.apply.call_count == 0
    assert game_state.uncertainEvents == []
    assert game_state.futureEvents == [event, event2]

    #Jump forward in time (and reset timer mock)
    timerHandler = gameState.Timer.call_args[0][1]
    gameState.Timer.reset_mock()
    monkeypatch.setattr('time.time', lambda: 200)

    #call the timer handler
    timerHandler()

    assert gameState.Timer.return_value.cancel.call_count == 0
    assert gameState.Timer.call_count == 1
    assert event.apply.call_count == 1
    assert event2.apply.call_count == 0
    assert game_state.uncertainEvents == [event]
    assert game_state.futureEvents == [event2]

def test_handle_future_event_timer_concurrent_events(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(150)
    mocker.spy(event, "apply")

    event2 = GameEvent(150)
    mocker.spy(event2, "apply")

    #Add the future event
    game_state.addEvent(event)
    game_state.addEvent(event2)

    assert gameState.Timer.call_args_list == [call(50, ANY), call(50, ANY)]
    assert event.apply.call_count == 0
    assert game_state.uncertainEvents == []
    assert game_state.futureEvents == [event, event2]

    #Jump forward in time (and reset timer mock)
    timerHandler = gameState.Timer.call_args[0][1]
    gameState.Timer.reset_mock()
    gameState.Timer.return_value.cancel.reset_mock()
    monkeypatch.setattr('time.time', lambda: 200)

    #call the timer handler
    timerHandler()

    assert gameState.Timer.return_value.cancel.call_count == 0
    assert gameState.Timer.call_count == 0
    assert event.apply.call_count == 1
    assert event2.apply.call_count == 1
    assert game_state.uncertainEvents == [event, event2]
    assert game_state.futureEvents == []