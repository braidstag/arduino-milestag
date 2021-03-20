from time import time
from falcon import HTTPBadRequest
import json


class GameResource:
    def __init__(self, game_state, game_logic):
        self.gameState = game_state
        self.gameLogic = game_logic

    def on_get(self, _req, resp):
        """Handles GET requests"""
        game = {
            'started': self.gameState.isGameStarted(),
            'gameEndTime': self.gameState.gameEndTime(),
            'targetTeamCount': self.gameState.withCurrGameState(lambda s: s.targetTeamCount),
            'gameTime': self.gameState.withCurrGameState(lambda s: s.gameTime),
            'teamPoints': self.gameState.withCurrGameState(lambda s: s.stats.teamPoints),
        }

        # resp.media = {key: value for key, value in game.items() if value is not None}
        resp.body = json.dumps({key: value for key, value in game.items() if value is not None})

    def on_patch(self, req, _resp):
        """Handles PATCH requests which change game settings/state"""

        req_obj = json.load(req.stream)

        if 'started' in req_obj:
            if req_obj['started']:
                # start game
                self.gameLogic.startGame(time())
            else:
                # stop game
                self.gameLogic.stopGame(time())

        if 'targetTeamCount' in req_obj:
            self.gameState.setTargetTeamCount(int(req_obj['targetTeamCount']))

        if 'gameTime' in req_obj:
            self.gameState.setGameTime(int(req_obj['gameTime']))

    def on_delete(self, _req, _resp):
        if not self.gameState.isGameStarted():
            self.gameLogic.resetGame(time())
        else:
            raise HTTPBadRequest(title='Cannot reset while game is started')
