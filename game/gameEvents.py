from core import Player, StandardGameLogic, ClientServer, GameState

class GameEvent(object):
    """An event in the game. Not to be confused with the class representing the string passed over the wire between client and server"""
    def __init__(self, serverTime):
        self.serverTime = serverTime
        self.logic = StandardGameLogic()

    def apply(self, gameState):
        """apply the effects of this event to the gamestate. This should be overridden by subclasses."""
        pass

class ClientGameEvent(GameEvent):
    def __init__(self, serverTime, recvTeam, recvPlayer):
        super(ClientGameEvent, self).__init__(serverTime)
        self.recvPlayer = recvPlayer
        self.recvTeam = recvTeam


class FireEvent(ClientGameEvent):
    def apply(self, gameState):
        player = gameState.getOrCreatePlayer(self.recvTeam, self.recvPlayer)
        if (self.logic.trigger(gameState, player)):
            #TODO: don't emit here.
            gameState.playerUpdated.emit(self.recvTeam, self.recvPlayer)

class FullAmmoEvent(ClientGameEvent):
    def apply(self, gameState):
        player = gameState.getOrCreatePlayer(self.recvTeam, self.recvPlayer)
        if (self.logic.fullAmmo(gameState, player)):
            #TODO: don't emit here.
              gameState.playerUpdated.emit(self.recvTeam, self.recvPlayer)

class HitEvent(ClientGameEvent):
    def __init__(self, serverTime, recvTeam, recvPlayer, sentTeam, sentPlayer, damage):
        super(HitEvent, self).__init__(serverTime, recvTeam, recvPlayer)
        self.sentTeam = sentTeam
        self.sentPlayer = sentPlayer
        self.damage = damage

    def apply(self, gameState):
        recvPlayer = gameState.getOrCreatePlayer(self.recvTeam, self.recvPlayer)
        sentPlayer = gameState.getOrCreatePlayer(self.sentTeam, self.sentPlayer)

        self.logic.hit(gameState, recvPlayer, sentPlayer, self.damage)
        #TODO: don't emit here.
        gameState.playerUpdated.emit(self.recvTeam, self.recvPlayer)