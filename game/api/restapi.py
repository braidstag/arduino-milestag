from threading import Thread

import falcon
from wsgiref import simple_server

from api.game import GameResource
from api.playerApi import PlayerResource, PlayerListResource
from api.helpers import CORSMiddleware


SERVER = '127.0.0.1'
PORT = 8000

def create_api(gameState, gameLogic):
  api = falcon.API(middleware=[CORSMiddleware()])

  api.add_route('/game', GameResource(gameState, gameLogic))

  api.add_route('/players', PlayerListResource(gameState))
  api.add_route('/players/{teamId:int}/{playerId:int}', PlayerResource(gameState))

  return api;

class RestApiThread(Thread):
  """
  A thread which serves a REST API.
  The rest api presents a view of the player and game state after the business logic has been applied
  """
  def __init__(self, gameState, gameLogic):
    super(RestApiThread, self).__init__(group=None)
    self.name = "REST API Thread"
    self.gameState = gameState
    self.gameLogic = gameLogic

  def run(self):
    api = create_api(self.gameState, self.gameLogic);

    self.httpd = simple_server.make_server(SERVER, PORT, api)
    print ("Starting REST server on http://" + SERVER + ":" + str(PORT))

    self.httpd.serve_forever(2)

  def stop(self):
      self.httpd.shutdown()
