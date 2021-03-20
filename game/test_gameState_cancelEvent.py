# pylint:disable=redefined-outer-name,E1101
import pytest

from gameState import GameState
from gameEvents import GameEvent


@pytest.fixture
def game_state():
    gameState = GameState()
    return gameState


def test_cancel_event(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    mocker.spy(event, "apply")

    event2 = GameEvent(60)
    mocker.spy(event2, "apply")

    event3 = GameEvent(150)
    mocker.spy(event3, "apply")

    event4 = GameEvent(160)
    mocker.spy(event4, "apply")

    game_state.uncertainEvents = [event, event2]
    game_state.futureEvents = [event3, event4]

    game_state.cancelEvent(lambda e: e is event or e is event3)

    assert event.apply.call_count == 0
    assert event2.apply.call_count == 1
    assert event3.apply.call_count == 0
    assert event4.apply.call_count == 0
    assert game_state.uncertainEvents == [event2]
    assert game_state.futureEvents == [event4]


def test_cancel_only_future_event(game_state, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    event = GameEvent(50)
    mocker.spy(event, "apply")

    event2 = GameEvent(60)
    mocker.spy(event2, "apply")

    event3 = GameEvent(150)
    mocker.spy(event3, "apply")

    event4 = GameEvent(160)
    mocker.spy(event4, "apply")

    game_state.uncertainEvents = [event, event2]
    game_state.futureEvents = [event3, event4]

    game_state.cancelEvent(lambda e: e is event3)

    assert event.apply.call_count == 0
    assert event2.apply.call_count == 0
    assert event3.apply.call_count == 0
    assert event4.apply.call_count == 0
    assert game_state.uncertainEvents == [event, event2]
    assert game_state.futureEvents == [event4]
