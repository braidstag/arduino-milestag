from threading import Thread

import falcon
from wsgiref import simple_server

import os
import mimetypes


from core import ClientServer
from api.game import GameResource
from api.playerApi import PlayerResource, PlayerListResource
from api.helpers import CORSMiddleware

def create_api(gameState, gameLogic, appPath):
  api = falcon.API() #middleware=[CORSMiddleware()])

  #server the admin-webapp on / if we have it
  if appPath:
    api.add_sink(staticResource(appPath), '/')

  api.add_route('/game', GameResource(gameState, gameLogic))

  api.add_route('/players', PlayerListResource(gameState))
  api.add_route('/players/{teamId:int}/{playerId:int}', PlayerResource(gameState))

  return api;

class RestApiThread(Thread):
  """
  A thread which serves a REST API.
  The rest api presents a view of the player and game state after the business logic has been applied
  """
  def __init__(self, gameState, gameLogic, appPath=None):
    super(RestApiThread, self).__init__(group=None)
    self.name = "REST API Thread"
    self.gameState = gameState
    self.gameLogic = gameLogic
    self.appPath = appPath

  def run(self):
    api = create_api(self.gameState, self.gameLogic, self.appPath);

    self.httpd = simple_server.make_server(ClientServer.SERVER, ClientServer.APIPORT, api)
    print ("Starting REST server on http://" + ClientServer.SERVER + ":" + str(ClientServer.APIPORT))

    self.httpd.serve_forever(2)

  def stop(self):
    self.httpd.shutdown()

def staticResource(appPath):
  def on_get(req, resp):
    name = req.path.strip()[1:];
    if name == '':
      name = 'index.html'

    resp.content_type = mimetypes.guess_type(name)[0]
    image_path = os.path.join(appPath, name)
    resp.stream = open(image_path, 'rb')
    resp.stream_len = os.path.getsize(image_path)
  return on_get

