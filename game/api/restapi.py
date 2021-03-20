from threading import Thread

import falcon
from wsgiref import simple_server

import os
import mimetypes

from core import ClientServer
from api.game import GameResource
from api.playerApi import PlayerResource, PlayerListResource, PlayerInitialisationResource
# from api.helpers import CORSMiddleware


def create_api(game_state, game_logic, listening_thread, app_path):
    api = falcon.API()  # middleware=[CORSMiddleware()])

    # server the admin-webapp on / if we have it
    if app_path:
        api.add_sink(static_resource(app_path), '/')

    api.add_route('/game', GameResource(game_state, game_logic))

    api.add_route('/players', PlayerListResource(game_state))
    api.add_route('/players/{teamId:int}/{playerId:int}', PlayerResource(game_state))
    api.add_route('/players:startInitialising', PlayerInitialisationResource(listening_thread))

    return api


class RestApiThread(Thread):
    """
    A thread which serves a REST API.
    The rest api presents a view of the player and game state after the business logic has been applied
    """
    def __init__(self, game_state, game_logic, listening_thread, app_path=None):
        super(RestApiThread, self).__init__(group=None)
        self.name = "REST API Thread"
        self.gameState = game_state
        self.gameLogic = game_logic
        self.listening_thread = listening_thread
        self.appPath = app_path
        self.httpd = None

    def run(self):
        api = create_api(self.gameState, self.gameLogic, self.listening_thread, self.appPath)

        self.httpd = simple_server.make_server(ClientServer.SERVER, ClientServer.APIPORT, api)
        print ("Starting REST server on http://" + ClientServer.SERVER + ":" + str(ClientServer.APIPORT))

        self.httpd.serve_forever(2)

    def stop(self):
        self.httpd.shutdown()


def static_resource(app_path):
    def on_get(req, resp):
        name = req.path.strip()[1:]
        if name == '':
            name = 'index.html'

        resp.content_type = mimetypes.guess_type(name)[0]
        image_path = os.path.join(app_path, name)
        resp.stream = open(image_path, 'rb')
        resp.stream_len = os.path.getsize(image_path)
    return on_get
