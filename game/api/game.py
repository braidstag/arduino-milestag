from time import time
from falcon import HTTPBadRequest

class GameResource:
    def __init__(self, gameState, gameLogic):
        self.gameState = gameState
        self.gameLogic = gameLogic

    def on_get(self, req, resp):
        """Handles GET requests"""
        game = {
            'started': self.gameState.isGameStarted(),
            'gameEndTime': self.gameState.gameEndTime(), #TODO: how do I omit this if it is None
            'targetTeamCount': self.gameState.withCurrGameState(lambda s: s.targetTeamCount),
            'gameTime': self.gameState.withCurrGameState(lambda s: s.gameTime),
        }

        resp.media = game

    def on_patch(self, req, resp):
        """Handles PATCH requests which change game settings/state"""
        if 'started' in req.media:
            if req.media['started']:
                #start game
                self.gameLogic.startGame(time())
            else:
                #stop game
                self.gameLogic.stopGame(time())

        if 'targetTeamCount' in req.media:
            self.gameState.setTargetTeamCount(int(req.media['targetTeamCount']))

        if 'gameTime' in req.media:
            self.gameState.setGameTime(int(req.media['gameTime']))

    def on_delete(self, req, resp):
        if not self.gameState.isGameStarted():
            self.gameLogic.resetGame(time())
        else:
            raise HTTPBadRequest(title = 'Cannot reset while game is started')
