# pylint:disable=redefined-outer-name,E1101
import pytest

from gameState import GameState


@pytest.fixture
def game_state():
    gameState = GameState()
    return gameState


def test_get_player_parameter(game_state, mocker):

    mocker.patch.object(game_state.currGameState.parameters, "getPlayerValue", autospec=True)
    game_state.currGameState.parameters.getPlayerValue.return_value = 42

    player = game_state.getOrCreatePlayer(1, 1)

    assert game_state.getPlayerParameter(player, "maxLength") == 42

    game_state.currGameState.parameters.getPlayerValue.assert_called_once_with("maxLength", 1, 1)
