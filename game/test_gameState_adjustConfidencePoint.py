# pylint:disable=redefined-outer-name,E1101
import pytest
import time
from mock import call, ANY

from gameState import GameState
from gameEvents import GameEvent

import gameState

@pytest.fixture
def game_state():
    gameState = GameState()
    return gameState

def test_adjust_no_events(game_state):
    game_state.getOrCreatePlayer(1,1)
    original_gameState = game_state.currGameState
    original_baselineGameState = game_state.baselineGameState

    game_state.adjustConfidencePoint(70)

    assert game_state.confidencePoint == 70
    assert original_gameState is game_state.currGameState
    assert original_baselineGameState is game_state.baselineGameState

def test_adjust_after_one_event(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)
    game_state.getOrCreatePlayer(1,1)
    original_gameState = game_state.currGameState

    event = GameEvent(50)
    mocker.spy(event, "apply")
    game_state.uncertainEvents = [event]

    game_state.adjustConfidencePoint(70)

    assert game_state.confidencePoint == 70
    assert game_state.uncertainEvents == []
    assert event.apply.call_count == 0
    assert original_gameState is game_state.currGameState
    assert original_gameState == game_state.baselineGameState
    assert not (original_gameState is game_state.baselineGameState)

def test_adjust_before_one_event(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)
    game_state.getOrCreatePlayer(1,1)
    original_gameState = game_state.currGameState
    original_baselineGameState = game_state.baselineGameState

    event = GameEvent(50)
    mocker.spy(event, "apply")
    game_state.uncertainEvents = [event]

    game_state.adjustConfidencePoint(30)

    assert game_state.confidencePoint == 30
    assert game_state.uncertainEvents == [event]
    assert event.apply.call_count == 0
    assert original_gameState is game_state.currGameState
    assert original_baselineGameState is game_state.baselineGameState

def test_adjust_between_events(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)
    game_state.getOrCreatePlayer(1,1)
    original_gameState = game_state.currGameState
    original_baselineGameState = game_state.baselineGameState

    event = GameEvent(50)
    mocker.spy(event, "apply")
    event2 = GameEvent(60)
    mocker.spy(event2, "apply")
    game_state.uncertainEvents = [event, event2]

    game_state.adjustConfidencePoint(55)

    assert game_state.confidencePoint == 55
    assert game_state.uncertainEvents == [event2]
    assert event.apply.call_count == 1
    assert event2.apply.call_count == 0
    assert original_gameState is game_state.currGameState
    assert  not (original_gameState is game_state.baselineGameState)
    assert original_baselineGameState is game_state.baselineGameState
