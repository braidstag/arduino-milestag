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
    gameState = mocker.MagicMock()
    gameState.withCurrGameState.side_effect = lambda x: x(current_game_state)

    return gameState

@pytest.fixture()
def game_logic(mocker):
    return mocker.MagicMock()

@pytest.fixture()
def client(game_state, game_logic):
    return testing.TestClient(create_api(game_state, game_logic))

@pytest.fixture()
def game_resource(game_state, game_logic):
    return GameResource(game_state, game_logic)

def test_get(game_state, game_logic, current_game_state, client, monkeypatch, mocker):

    gameEndTime = time.time() + 1140;

    game_state.isGameStarted.return_value = False
    game_state.gameEndTime.return_value = gameEndTime
    current_game_state.targetTeamCount = 2
    current_game_state.gameTime = 1200

    result = client.simulate_get('/game')

    assert result.json == {
        u'gameEndTime': gameEndTime,
        u'gameTime': 1200,
        u'started': False,
        u'targetTeamCount': 2
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