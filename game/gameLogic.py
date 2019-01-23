from __future__ import print_function
from gameEvents import FireEvent, HitEvent, GameStartedEvent, GameEndedEvent, SetMainPlayerEvent

class GameLogic(object):
    def __init__(self, gameState):
        super(GameLogic, self).__init__()
        self.gameState = gameState

    def trigger(self, serverTime, recvTeam, recvPlayer):
        self.gameState.addEvent(FireEvent(serverTime, recvTeam, recvPlayer))

    def triggerRelease(self, serverTime, recvTeam, recvPlayer):
        #cancel all fire events after we release the trigger.
        self.gameState.cancelEvent(lambda e: isinstance(e, FireEvent) and e.serverTime > serverTime)

    def hit(self, serverTime, recvTeam, recvPlayerId, sentTeam, sentPlayerId, damage):
        self.gameState.addEvent(HitEvent(serverTime, recvTeam, recvPlayerId, sentTeam, sentPlayerId, damage))

    #TODO: should we take serverTime or just use time.time()
    def startGame(self, serverTime, duration = 0):
        self.gameState.addEvent(GameStartedEvent(serverTime, duration))

    def stopGame(self, serverTime):
        self.gameState.cancelEvent(lambda e: isinstance(e, GameEndedEvent) and e.serverTime > serverTime)
        self.gameState.addEvent(GameEndedEvent(serverTime))

    #TODO:
    def resetGame(self, serverTime):
        pass

    #############
    #Client Only
    def setMainPlayer(self, serverTime, player):
        self.gameState.addEvent(SetMainPlayerEvent(serverTime, player))

    def setSnapshot(self, serverTime, player):
        self.gameState.addEvent(SetMainPlayerEvent(serverTime, player))