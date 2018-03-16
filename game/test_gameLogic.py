#!/usr/bin/python

import pytest

from core import Player, StandardGameLogic, GameState
from server import ServerMsgHandler, ServerGameState

# pylint:disable=redefined-outer-name

@pytest.fixture
def game_state():
    gameState = GameState()
    gameState.setGameTime(120)
    return gameState

@pytest.fixture
def game_logic():
    return StandardGameLogic()

def test_simple_hit_from_dead_player(game_state, game_logic):
    game_state.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentPlayer = Player(1, 2)
    sentPlayer.health = 0
    damage = 2
  
    game_logic.hit(game_state, player, sentPlayer, damage)
  
    assert initialHealth == player.health

def test_simple_hit_while_game_stopped(game_state, game_logic):
    player = Player(1, 1)
    initialHealth = player.health
  
    sentPlayer = Player(1, 2)
    damage = 2
  
    game_logic.hit(game_state, player, sentPlayer, damage)
  
    assert initialHealth == player.health

def test_simple_hit(game_state, game_logic):
    game_state.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentPlayer = Player(2, 1)
    damage = 2
  
    game_logic.hit(game_state, player, sentPlayer, damage)
  
    assert initialHealth - damage == player.health

def test_self_hit(game_state, game_logic):
    game_state.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentPlayer = Player(1, 1)
    damage = 2
  
    game_logic.hit(game_state, player, sentPlayer, damage)
  
    assert initialHealth == player.health

def test_team_hit(game_state, game_logic):
    game_state.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentPlayer = Player(1, 2)
    damage = 2
  
    game_logic.hit(game_state, player, sentPlayer, damage)
  
    assert initialHealth - damage == player.health

def test_shot_until_dead(game_state, game_logic):
    game_state.startGame()
    player = Player(1, 1)
    initialHealth = player.health
  
    sentPlayer = Player(2, 1)
    damage = (player.health // 2) + 1 # this will fail if the player only starts with 2 health :-(
  
    game_logic.hit(game_state, player, sentPlayer, damage)
    assert initialHealth - damage == player.health

    game_logic.hit(game_state, player, sentPlayer, damage)
    assert 0 == player.health
    
    game_logic.hit(game_state, player, sentPlayer, damage)
    assert 0 == player.health