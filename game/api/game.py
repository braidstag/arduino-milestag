from time import time
from falcon import HTTPBadRequest
import json

class GameResource:
    def __init__(self, gameState, gameLogic):
        self.gameState = gameState
        self.gameLogic = gameLogic

    def on_get(self, req, resp):
        """Handles GET requests"""
        game = {
            'started': self.gameState.isGameStarted(),
            'gameEndTime': self.gameState.gameEndTime(),
            'targetTeamCount': self.gameState.withCurrGameState(lambda s: s.targetTeamCount),
            'gameTime': self.gameState.withCurrGameState(lambda s: s.gameTime),
            'teamPoints': self.gameState.withCurrGameState(lambda s: s.stats.teamPoints),
        }

        #resp.media = {key: value for key, value in game.items() if value is not None}
        resp.body = json.dumps({key: value for key, value in game.items() if value is not None})

    def on_patch(self, req, resp):
        """Handles PATCH requests which change game settings/state"""

        reqObj = json.load(req.stream)

        if 'started' in reqObj:
            if reqObj['started']:
                #start game
                self.gameLogic.startGame(time())
            else:
                #stop game
                self.gameLogic.stopGame(time())

        if 'targetTeamCount' in reqObj:
            self.gameState.setTargetTeamCount(int(reqObj['targetTeamCount']))

        if 'gameTime' in reqObj:
            self.gameState.setGameTime(int(reqObj['gameTime']))

    def on_delete(self, req, resp):
        if not self.gameState.isGameStarted():
            self.gameLogic.resetGame(time())
        else:
            raise HTTPBadRequest(title = 'Cannot reset while game is started')
