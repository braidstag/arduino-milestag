def extractPlayerInfo(currentGameState, player, fullInfo = True):
    playerObj = {
        'teamId': player.teamID,
        'playerId': player.playerID,
        'ammo': player.ammo,
        'health': player.health,
    }

    if fullInfo:
        params = currentGameState.parameters.getPlayerParameters(player.teamID, player.playerID)['parameters']

        for p in params:
            params[p]['currentValue'] = currentGameState.parameters._getValue(p, str(player.teamID) + "/" + str(player.playerID))

        playerObj['parameters'] = params

    return playerObj


class PlayerListResource:
    def __init__(self, gameState):
        self.gameState = gameState

    def on_get(self, req, resp):
        fullInfo = False
        try:
            fullInfo = req.params['fullInfo'].lower() == 'true'
        except:
            pass

        playerList = {
            'players': self.gameState.withCurrGameState(lambda cgs: [extractPlayerInfo(cgs, player, fullInfo) for player in cgs.players.values()]),
        }

        resp.media = playerList

class PlayerResource:
    def __init__(self, gameState):
        self.gameState = gameState

    def on_get(self, req, resp, teamId, playerId):

        player = self.gameState.withCurrGameState(lambda cgs: extractPlayerInfo(cgs, cgs.players[(teamId, playerId)]))
        resp.media = player
        #TODO handle 404

    def on_patch(self, req, resp, teamId, playerId):
        pass
