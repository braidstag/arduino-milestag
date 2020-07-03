from __future__ import print_function
from gameState import CS_OFFLINE, CS_UNINITIALISED, CS_INITIALISING, CS_ESTABLISHED
from player import Player, Stats as PlayerStats

class GameEvent(object):
    """An event in the game. Not to be confused with the class representing the string passed over the wire between client and server"""
    def __init__(self, serverTime):
        self.serverTime = serverTime

    def apply(self, gameState):
        """ Apply the effects of this event to the gamestate.

            If this event would like to add a subsequent event it should return it
            the first time this is called but not subsequently (e.g. an event which repeats)

            This should be overridden by subclasses.
        """
        pass

class GameStartedEvent(GameEvent):
    def __init__(self, serverTime, duration):
        super(GameStartedEvent, self).__init__(serverTime)
        self.duration = duration
        self.createdNextEvent = False

    def apply(self, gameState):
        duration = self.duration
        if duration == 0:
            duration = gameState.withCurrGameState(lambda s: s.gameTime)

        gameEndTime = self.serverTime + duration
        gameState.startGame(gameEndTime)

        if not self.createdNextEvent:
            #TODO: If duration changes from when we first applied this, the stop won't be adjusted accordingly.
            # Perhaps when re-applying we should disregard subsequent events and re-add them
            # We would need to handle this when re-baselining though.

            #Add the next event
            self.createdNextEvent = True
            return GameEndedEvent(gameEndTime)

class GameEndedEvent(GameEvent):
    def __init__(self, serverTime):
        super(GameEndedEvent, self).__init__(serverTime)

    def apply(self, gameState):
        gameState.endGame()

class ClientGameEvent(GameEvent):
    """An event caused by something the client is reporting"""
    def __init__(self, serverTime, recvTeam, recvPlayer):
        super(ClientGameEvent, self).__init__(serverTime)
        self.recvPlayerId = recvPlayer
        self.recvTeam = recvTeam

class FireEvent(ClientGameEvent):
    repeatRate = 1 #seconds per shot

    def __init__(self, serverTime, recvTeam, recvPlayerId):
        super(FireEvent, self).__init__(serverTime, recvTeam, recvPlayerId)
        self.firstApplication = True

    def apply(self, gameState):
        if gameState.isClient:
            if gameState.clientState == CS_OFFLINE or gameState.clientState == CS_UNINITIALISED:
                # We havn't connected to the server or havn't been told we can fire yet. So just ignore this.
                return
            elif gameState.clientState == CS_INITIALISING:
                # We are initialising so should fire but don't have a proper player yet.
                # just tell the gun to fire the IR.
                gameState.notifyFiredListeners()
                return
            else:
                # We know what player we are so proceed as normal.
                player = gameState.getMainPlayer()
        else:
            player = gameState.getOrCreatePlayer(self.recvTeam, self.recvPlayerId)

        if not gameState.isGameStarted():
            #nothing to do
            # TODO: should we repeat?
            return

        #print("Applying FireEvent to", player)

        if player.ammo > 0 and player.health > 0:
            player = Player(copyFrom = player, ammo = player.ammo - 1)

            if not gameState.isClient:
                player = Player(copyFrom = player, stats = {'shotsFired': player.stats.shotsFired + 1})

            gameState.currGameState.players[(player.teamID, player.playerID)] = player

            #Let listeners know this has just been processed
            gameState.notifyFiredListeners()
            #TODO: lookup repeatRate from the player and what their gun does.
            if self.repeatRate > 0 and self.firstApplication:
                #Add the next event
                self.firstApplication = False
                return FireEvent(self.serverTime + self.repeatRate, self.recvTeam, self.recvPlayerId)

class HitEvent(ClientGameEvent):
    def __init__(self, serverTime, recvTeam, recvPlayerId, sentTeam, sentPlayerId, damage):
        super(HitEvent, self).__init__(serverTime, recvTeam, recvPlayerId)
        self.sentTeam = sentTeam
        self.sentPlayerId = sentPlayerId
        self.damage = damage

    def apply(self, gameState):
        if gameState.isClient:
            if gameState.clientState != CS_ESTABLISHED:
                # Don't apply a hit to an uninitialised player.
                return
            toPlayer = gameState.getMainPlayer()
        else:
            toPlayer = gameState.getOrCreatePlayer(self.recvTeam, self.recvPlayerId)
            fromPlayer = gameState.getOrCreatePlayer(self.sentTeam, self.sentPlayerId)

        if not gameState.isGameStarted():
            print("hit before game started")
        elif (self.recvPlayerId == self.sentPlayerId and self.recvTeam == self.sentTeam):
            #self shot, ignore this
            pass
        elif not gameState.isClient and fromPlayer.health <= 0:
            #shooting player is already dead, don't count this if we're the server.
            pass
        else:
            origToPlayer = toPlayer
            toPlayer = toPlayer.reduceHealth(self.damage)
            died = origToPlayer != toPlayer and toPlayer.health == 0
            if not gameState.isClient:
                toPlayer = Player(copyFrom=toPlayer, stats = {'hitsReceived': toPlayer.stats.hitsReceived + 1})
                fromPlayer = Player(copyFrom=fromPlayer, stats = {'hitsGiven': fromPlayer.stats.hitsGiven + 1})

                if (died):
                    toPlayer = Player(copyFrom=toPlayer, stats = {'deaths': toPlayer.stats.deaths + 1})
                    fromPlayer = Player(copyFrom=fromPlayer, stats = {'kills': fromPlayer.stats.kills + 1})

                    # update team scores separately to player scores as they might change team and shouldn't take their points with them.
                    def giveTeamPoint(cgs):
                        if fromPlayer.teamID in cgs.stats.teamPoints:
                            cgs.stats.teamPoints[fromPlayer.teamID] = cgs.stats.teamPoints[fromPlayer.teamID] + 1
                        else:
                            cgs.stats.teamPoints[fromPlayer.teamID] = 1
                    gameState.withCurrGameState(giveTeamPoint)
                gameState.currGameState.players[(self.sentTeam, self.sentPlayerId)] = fromPlayer
            gameState.currGameState.players[(toPlayer.teamID, toPlayer.playerID)] = toPlayer

#############
# Client Only
class SetMainPlayerEvent(GameEvent):
    def __init__(self, serverTime, player):
        super(SetMainPlayerEvent, self).__init__(serverTime)
        self.player = player

    def apply(self, gameState):
        gameState.setMainPlayer(self.player)

class SetParametersEvent(GameEvent):
    def __init__(self, serverTime, parameters):
        super(SetParametersEvent, self).__init__(serverTime)
        self.parameters = parameters

    def apply(self, gameState):
        gameState.setParameters(self.parameters)