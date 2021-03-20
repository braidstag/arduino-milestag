# pylint:disable=redefined-outer-name
import pytest
import time
from falcon import HTTPBadRequest, testing

from restapi import create_api
from game import GameResource


@pytest.fixture()
def current_game_state(mocker):
    return mocker.MagicMock()


@pytest.fixture()
def game_state(mocker, current_game_state):
    game_state = mocker.MagicMock()
    game_state.withCurrGameState.side_effect = lambda x: x(current_game_state)

    return game_state


@pytest.fixture()
def game_logic(mocker):
    return mocker.MagicMock()


def listening_thread(mocker):
    return mocker.MagicMock()


@pytest.fixture()
def client(game_state, game_logic, listening_thread):
    return testing.TestClient(create_api(game_state, game_logic, listening_thread, None))


@pytest.fixture()
def game_resource(game_state, game_logic):
    return GameResource(game_state, game_logic)


def test_get(game_state, game_logic, current_game_state, client, monkeypatch, mocker):

    game_end_time = time.time() + 1140

    game_state.isGameStarted.return_value = False
    game_state.gameEndTime.return_value = game_end_time
    current_game_state.targetTeamCount = 2
    current_game_state.gameTime = 1200
    current_game_state.stats.teamPoints = {1: 2, 2: 5}

    result = client.simulate_get('/game')

    assert result.json == {
        u'gameEndTime': game_end_time,
        u'gameTime': 1200,
        u'started': False,
        u'targetTeamCount': 2,
        u'teamPoints': {
            u'1': 2,
            u'2': 5
        }
    }

    assert result.status_code == 200


def test_get_no_game_end_time(game_state, game_logic, current_game_state, client, monkeypatch, mocker):

    game_state.isGameStarted.return_value = False
    game_state.gameEndTime.return_value = None
    current_game_state.targetTeamCount = 2
    current_game_state.gameTime = 1200
    current_game_state.stats.teamPoints = {1: 2, 2: 5}

    result = client.simulate_get('/game')

    assert result.json == {
        u'gameTime': 1200,
        u'started': False,
        u'targetTeamCount': 2,
        u'teamPoints': {
            u'1': 2,
            u'2': 5
        }
    }

    assert result.status_code == 200


def test_delete_resets(game_resource, game_state, game_logic):
    game_state.isGameStarted.return_value = False

    GameResource(game_state, game_logic).on_delete(None, None)
    game_logic.resetGame.assert_called_once()


def test_delete_errors(game_resource, game_state, game_logic):
    game_state.isGameStarted.return_value = True

    with pytest.raises(HTTPBadRequest):
        game_resource.on_delete(None, None)

    assert game_logic.resetGame.call_count == 0