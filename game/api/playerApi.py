import json
from falcon import HTTPBadRequest


def extractPlayerInfo(current_game_state, player, full_info=True):
    player_obj = {
        'teamId': player.team_id,
        'playerId': player.player_id,
        'ammo': player.ammo,
        'health': player.health,
    }

    if full_info:
        params = current_game_state.parameters.getPlayerParameters(player.team_id, player.player_id)['parameters']

        for p in params:
            params[p]['currentValue'] = current_game_state.parameters._getValue(p, str(player.team_id) + "/" + str(player.player_id))

        player_obj['parameters'] = params
        player_obj['stats'] = player.stats.toSimpleTypes()

    return player_obj


class PlayerListResource:
    def __init__(self, game_state):
        self.gameState = game_state

    def on_get(self, req, resp):
        full_info = False
        try:
            full_info = req.params['fullInfo'].lower() == 'true'
        except:
            pass

        player_list = {
            'players': self.gameState.withCurrGameState(lambda cgs: [extractPlayerInfo(cgs, player, full_info) for player in cgs.players.values()]),
        }

        # resp.media = playerList
        resp.body = json.dumps(player_list)


class PlayerResource:
    def __init__(self, game_state):
        self.gameState = game_state

    def on_get(self, _req, resp, team_id, player_id):

        player = self.gameState.withCurrGameState(lambda cgs: extractPlayerInfo(cgs, cgs.players[(team_id, player_id)]))
        # resp.media = player
        resp.body = json.dumps(player)
        # TODO handle 404

    def on_patch(self, req, resp, team_id, player_id):
        pass


class PlayerInitialisationResource:
    def __init__(self, listening_thread):
        self.listening_thread = listening_thread

    def on_post(self, _req, _resp):
        try:
            connection = self.listening_thread.uninitialisedConnections.pop()
        except KeyError:
            raise HTTPBadRequest(title='No player waiting to initialise')

        self.listening_thread.startInitialising(connection)

    def on_patch(self, req, resp, team_id, player_id):
        pass
