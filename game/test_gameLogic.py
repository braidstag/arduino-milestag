# pylint:disable=redefined-outer-name
import pytest
import time

from gameLogic import GameLogic
from gameState import GameState
from player import Player
from gameEvents import FireEvent

@pytest.fixture
def game_state():
    gameState = GameState()
    return gameState

@pytest.fixture
def game_logic(game_state):
    return GameLogic(game_state)

@pytest.fixture
def client_game_state():
    game_state = GameState()
    game_state.setMainPlayer(game_state.getOrCreatePlayer(1, 1))
    game_state.isClient = True

    return game_state

@pytest.fixture
def client_game_logic(client_game_state):
    return GameLogic(client_game_state)

def test_simple_hit_from_live_player(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    game_logic.startGame(50)
    player = game_state.getOrCreatePlayer(1, 1)
    initialHealth = player.health

    damage = 2

    game_logic.hit(100, 1, 1, 1, 2, damage)

    assert initialHealth > player.health

def test_simple_hit_from_live_player_client(client_game_state, client_game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    player = client_game_state.getMainPlayer()
    client_game_logic.startGame(50)
    initialHealth = player.health

    damage = 2

    client_game_logic.hit(100, None, None, 1, 2, damage)

    assert initialHealth > player.health

def test_simple_hit_from_live_player_before_game_starts(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    player = game_state.getOrCreatePlayer(1, 1)
    initialHealth = player.health

    damage = 2

    game_logic.hit(100, 1, 1, 1, 2, damage)

    assert initialHealth == player.health

def test_simple_hit_from_dead_player(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    game_logic.startGame(50)
    player = game_state.getOrCreatePlayer(1, 1)
    initialHealth = player.health

    sentPlayer = game_state.getOrCreatePlayer(1, 2)
    sentPlayer.health = 0
    damage = 2

    game_logic.hit(100, 1, 1, 1, 2, damage)

    assert initialHealth == player.health

def test_historic_hit_from_live_player(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    game_logic.startGame(100)
    player = game_state.getOrCreatePlayer(1, 1)
    initialHealth = player.health

    damage = 2

    game_logic.hit(50, 1, 1, 1, 2, damage)

    assert initialHealth == player.health

def test_hit_from_live_player_after_game_stops(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    game_logic.startGame(100)
    player = game_state.getOrCreatePlayer(1, 1)
    initialHealth = player.health

    damage = 2

    #fast-forward to after the game ends
    monkeypatch.setattr('time.time', lambda: 200 + game_state.currGameState.gameTime)
    game_state._recheckTimer()

    game_logic.hit(150 + game_state.currGameState.gameTime, 1, 1, 1, 2, damage)

    assert initialHealth == player.health

def test_simple_hit_from_self(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)

    game_logic.startGame(50)
    player = game_state.getOrCreatePlayer(1, 1)
    initialHealth = player.health

    damage = 2

    game_logic.hit(100, 1, 1, 1, 1, damage)

    assert initialHealth == player.health

def test_addHitEvent_outOfOrder(game_state, game_logic, monkeypatch, mocker):
    "Test handling of a subsequent, earlier event"

    monkeypatch.setattr('time.time', lambda: 300)

    game_state.getOrCreatePlayer(1, 1)
    game_state.getOrCreatePlayer(2, 1)
    game_logic.startGame(50)

    game_logic.hit(200, 2, 1, 1, 1, 999)

    assert game_state.currGameState.players[(1, 1)].health > 0
    assert game_state.currGameState.players[(2, 1)].health == 0

    game_logic.hit(100, 1, 1, 2, 1, 999)

    assert game_state.currGameState.players[(1, 1)].health == 0
    assert game_state.currGameState.players[(2, 1)].health > 0

def test_simple_fire(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)
    FireEvent.repeatRate = 0

    game_logic.startGame(50)
    player = game_state.getOrCreatePlayer(1, 1)
    initialAmmo = player.ammo

    game_logic.trigger(100, 1, 1)

    assert initialAmmo - 1 == player.ammo

def test_simple_fire_client(client_game_state, client_game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)
    FireEvent.repeatRate = 0

    player = client_game_state.getMainPlayer()
    client_game_logic.startGame(50)
    initialAmmo = player.ammo

    client_game_logic.trigger(100, None, None)

    assert initialAmmo - 1 == player.ammo

def test_repeat_fire(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)
    FireEvent.repeatRate = 20

    game_logic.startGame(30)
    player = game_state.getOrCreatePlayer(1, 1)
    initialAmmo = player.ammo

    game_logic.trigger(50, 1, 1)

    assert initialAmmo - 3 == player.ammo
    assert isinstance(game_state.futureEvents[1], FireEvent)

def test_repeat_fire_stop(game_state, game_logic, monkeypatch, mocker):
    monkeypatch.setattr('time.time', lambda: 100)
    mocker.patch("gameState.Timer", autospec=True)
    FireEvent.repeatRate = 20

    game_logic.startGame(30)
    player = game_state.getOrCreatePlayer(1, 1)
    initialAmmo = player.ammo

    game_logic.trigger(50, 1, 1)
    game_logic.triggerRelease(80, 1, 1)

    player = game_state.getOrCreatePlayer(1, 1)
    assert initialAmmo - 2 == player.ammo
    assert len(game_state.futureEvents) == 1

#TODO: Should this be a unit test?

# def test_detectAndHandleClockDrift(msg_handler, server, game_state, mocker):
#     server.timeProvider.return_value = 300
#     assert msg_handler.handleMsg("E(123def,1200,Pong(100,0))", server)
#     server.timeProvider.return_value = 400
#     mocker.spy(game_state, "addEvent")
#     assert msg_handler.handleMsg("E(123def,1300,H2,1,3)", server)

#     assert game_state.addEvent.call_count == 1
#     assert game_state.addEvent.call_args[0][0].serverTime == 300
