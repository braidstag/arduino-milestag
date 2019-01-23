from __future__ import print_function
import time
from copy import deepcopy
from threading import Timer, RLock

from player import Player

# initial game settings, these are told to the clients and can be changed in the UI.
TEAM_COUNT = 2

#TODO: Can we make this (and Player) immutable and have events create a new one based on their changes?
class MomentaryGameState(object):
    """The state of the game at any given moment in time.
    This is mutable and you should be careful that you only use instances of this
    class when it is guaranteed not to be being changed by another thread trying to
    recalculate the current state.
    """

    def __init__(self):
        #map from (team, player) to the Player instance
        self.players = {}
        self.teamCount = 0
        self.largestTeam = 0
        self.targetTeamCount = TEAM_COUNT

        self.gameStarted = False
        self.gameTime = 1200 #20 mins


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

class GameState(object):
    """A store of all of the gamestate which the server knows about.
    There is only one instance of this class on the server.

    This splits events into 3:
    * certain past events - these happened in the past and we are sure there
    are no events which we don't know about after these
    * uncertain past events - these happened in the past but there may be
    events we don't know about yet
    * future events - these events will happen in the future.

    We keep a baseline state which contains the result of all certain past events
    (and discard the certain past events themselves)
    We periodically re-baseline when we are confident that we have recieved
    all events up to a point (the confidence point) effectively moving events
    from the uncertain past to the certain past.

    We maintain a timer which applies future events when they are due,
    moving them to the uncertain past.
    """

    def __init__(self, isClient = False):
        self.isClient = isClient #immutable, are we using client or server logic

        self.currGameState = MomentaryGameState()
        self.baselineGameState = MomentaryGameState()
        self.stateLock = RLock()

        self.confidencePoint = 0
        self.uncertainEvents = []

        self.nextFutureEventTime = 0
        self.futureEvents = []
        self.nextFutureEventTimer = None

        self.pauseListeners = False
        self.stateChangedListeners = []
        self.playerAdjustedListeners = []
        self.playerMovedListeners = []
        self.gameStartedListeners = []
        self.gameStoppedListeners = []
        self.firedListeners = []

    ####################
    ## Players and teams

    def getOrCreatePlayer(self, sentTeam, sentPlayer):
        with self.stateLock:
            if not (sentTeam, sentPlayer) in self.currGameState.players:
                self.currGameState.players[(sentTeam, sentPlayer)] = Player(sentTeam, sentPlayer)
                if sentTeam > self.currGameState.teamCount:
                    self.currGameState.teamCount = sentTeam
                    # self.currGameState.teamCountChanged.emit(self.currGameState.teamCount)
                if sentPlayer > self.currGameState.largestTeam:
                    self.currGameState.largestTeam = sentPlayer
                    # self.currGameState.largestTeamChanged.emit(self.currGameState.largestTeam)

                #self.playerAdded.emit(sentTeam, sentPlayer)
            return self.currGameState.players[(sentTeam, sentPlayer)]

    def createNewPlayer(self):
        with self.stateLock:
            created_player = self._createNewPlayer0()
            self._notifyStateChangedListeners()
            return created_player

    def _createNewPlayer0(self):
        for playerID in range(1, 33):
            for teamID in range(1, self.currGameState.targetTeamCount + 1):
                if (teamID, playerID) not in self.currGameState.players:
                    return self.getOrCreatePlayer(teamID, playerID)

        # TODO handle this
        raise RuntimeError("too many players")


    def movePlayer(self, srcTeamID, srcPlayerID, dstTeamID, dstPlayerID):
        with self.stateLock:
            if (dstTeamID, dstPlayerID) in self.currGameState.players:
                raise RuntimeError("Tried to move a player to a non-empty spot")
            if (srcTeamID, srcPlayerID) not in self.currGameState.players:
                return

            player = self.currGameState.players[(srcTeamID, srcPlayerID)]
            self.currGameState.players[(dstTeamID, dstPlayerID)] = player
            player.teamID = dstTeamID
            player.playerID = dstPlayerID
            # TODO: should we reset their stats.
            del self.currGameState.players[(srcTeamID, srcPlayerID)]

            if dstTeamID > self.currGameState.teamCount:
                self.currGameState.teamCount = dstTeamID
                # self.currGameState.teamCountChanged.emit(self.currGameState.teamCount)

            if dstPlayerID > self.currGameState.largestTeam:
                self.currGameState.largestTeam = dstPlayerID
                # self.currGameState.largestTeamChanged.emit(self.currGameState.largestTeam)

            if srcTeamID == self.currGameState.teamCount:
                # check if this was the only player in this team
                self._recalculateTeamCount()

            if srcPlayerID == self.currGameState.largestTeam:
                # check if this was the only player in this team
                self._recalculateLargestTeam()

            self._notifyPlayerMovedListeners(srcTeamID, srcPlayerID, player)

        self._notifyStateChangedListeners()

    def deletePlayer(self, teamID, playerID):
        with self.stateLock:
            if (teamID, playerID) not in self.currGameState.players:
                return

            del self.currGameState.players[(teamID, playerID)]

            if teamID == self.currGameState.teamCount:
                # check if this was the only player in this team
                self._recalculateTeamCount()

            if playerID == self.currGameState.largestTeam:
                # check if this was the only player in this team
                self._recalculateLargestTeam()

        #self.listeningThread.deletePlayer(teamID, playerID)
        self._notifyStateChangedListeners()

    def _recalculateTeamCount(self):
        """ Recalculate the team count.
            Note that this won't detect if the teamCount is too low so only call this when players have been removed
        """
        with self.stateLock:
            self._recalculateTeamCount0()
            self._notifyStateChangedListeners()

    def _recalculateTeamCount0(self):
        """ Recalculate the team count.
            Note that this won't detect if the teamCount is too low so only call this when players have been removed
        """
        for teamID in range(self.currGameState.teamCount, 0, -1):
            for playerID in range(self.currGameState.largestTeam, 0, -1):
                if (teamID, playerID) in self.currGameState.players:
                    # still need this team
                    if self.currGameState.teamCount != teamID:
                        self.currGameState.teamCount = teamID

                    return

    def _recalculateLargestTeam(self):
        """ Recalculate the largest team.
            Note that this won't detect if the largestTeam is too low so only call this when players have been removed
        """
        with self.stateLock:
            self._recalculateLargestTeam0()
            self._notifyStateChangedListeners()

    def _recalculateLargestTeam0(self):
        """ Recalculate the largest team.
            Note that this won't detect if the largestTeam is too low so only call this when players have been removed
        """
        for playerID in range(self.currGameState.largestTeam, 0, -1):
            for teamID in range(self.currGameState.teamCount, 0, -1):
                if (teamID, playerID) in self.currGameState.players:
                    # one team still has this many players
                    if self.currGameState.largestTeam != playerID:
                        self.currGameState.largestTeam = playerID

                    return

    def setTargetTeamCount(self, value):
        with self.stateLock:
            self.currGameState.targetTeamCount = value
        self._notifyStateChangedListeners()

    def setGameTime(self, gameTime):
        with self.stateLock:
            self.currGameState.gameTime = gameTime
        self._notifyStateChangedListeners()

    def gameTimeRemaining(self):
        with self.stateLock:
            return self.currGameState.gameEndTime - time.time()

    #############################
    # Starting and stopping game

    def startGame(self, gameEndTime):
        with self.stateLock:
            self.currGameState.gameStarted = True
            self.currGameState.gameEndTime = gameEndTime

        self._notifyGameStartedListeners()

    def endGame(self):
        with self.stateLock:
            self.currGameState.gameStarted = False
            self.currGameState.gameEndTime = None

        self._notifyGameStoppedListeners()

    def isGameStarted(self):
        with self.stateLock:
            return self.currGameState.gameStarted

#   def resetGame(self):
#     #self.listeningThread.queueMessageToAll(proto.RESETGAME.create())
#     for p in self.currGameState.players.values():
#       p.reset()
#       #self.playerUpdated.emit(p.teamID, p.playerID)

    #############
    # Client Only

    def setMainPlayer(self, player):
        with self.stateLock:
            key = (player.teamID, player.playerID)
            self.currGameState.players[key] = deepcopy(player)
            self.currGameState.mainPlayer = key

        self._notifyStateChangedListeners()

    def getMainPlayer(self):
        #TODO: player is mutable, there is nothing preventing this being changed by our events system. We should do this as withMainPlayer(func)
        with self.stateLock:
            try:
                return self.currGameState.players[self.currGameState.mainPlayer]
            except (KeyError, AttributeError):
                return None

    def withCurrGameState(self, func):
        """Execute the func passing in the current state.
        This ensures the state is not being modified while the func runs.
        Don't leak references to currGameState, once func has finished, it might be in an inconsistent state.
        """
        with self.stateLock:
            return func(self.currGameState)


    #########
    # Events

    def addEvent(self, event):
        with self.stateLock:
            currentServerTime = time.time()
            if (event.serverTime > currentServerTime):
                self._addFutureEvent(event)
            else:
                self._addPastEvent(event)

    def _addFutureEvent(self, event):
        self.futureEvents.append(event)
        self._recheckTimer()

    def _recheckTimer(self):
        with self.stateLock:
            if (self.nextFutureEventTimer):
                self.nextFutureEventTimer.cancel()
                self.nextFutureEventTimer = None

            nextEvent = None
            currTime = time.time()
            # Process any overdue events and find the next future event
            for e in self.futureEvents[:]:
                if (e.serverTime <= currTime):
                    # remove from futureEvents then apply immediately
                    # Note this must be this way round as addEvent calls this
                    self.futureEvents.remove(e)
                    self.addEvent(e)
                else:
                    # check if this is the earliest event we have seen
                    if (not nextEvent or nextEvent.serverTime > e.serverTime):
                        nextEvent = e

            if (nextEvent):
                self.nextFutureEventTimer = Timer(
                    nextEvent.serverTime - currTime,
                    lambda: self._handleFutureEventTimer(nextEvent)
                    )
                self.nextFutureEventTimer.start()
                # print("Waiting until " + str(nextEvent.serverTime) + " for " + str(nextEvent))

    def _handleFutureEventTimer(self, nextEvent):
        with self.stateLock:
            # check that the times are still correct
            if (nextEvent.serverTime > time.time()):
                print("Timer woke us up before it was due. trying again")
            else:
                # print("Handling " + str(nextEvent) + " due to timer")
                #We are done with this timer now
                self.nextFutureEventTimer = None
                #Check whether we still want this event.
                if nextEvent in self.futureEvents:
                    # remove from futureEvents then apply immediately
                    # Note this must be this way round as addEvent calls this
                    self.futureEvents.remove(nextEvent)
                    self.addEvent(nextEvent)
            self._recheckTimer()

    def _addPastEvent(self, event):
        if (event.serverTime < self.confidencePoint):
            raise RuntimeError("Tried to add a new event which is prior to the current confidence point. This doesn't make sense as the confidence point is after all possible events.")
        elif (len(self.uncertainEvents) == 0 or (event.serverTime >= self.uncertainEvents[-1].serverTime)):
            # This is later than anything we have seen so far, just apply it now.
            self.uncertainEvents.append(event)
            newEvent = event.apply(self)
            if newEvent:
                self.addEvent(newEvent)
        else:
            # This needs to be inserted in the appropriate position in the uncertain events list and we need to recalculate our latest state by applying all uncertainEvents to the baseline
            newIndex = 0
            for e in self.uncertainEvents:
                if (event.serverTime > e.serverTime):
                    newIndex = newIndex + 1
                else:
                    break
            self.uncertainEvents.insert(newIndex, event)

            #Apply the event as if it happened last as a first approximation and the re-apply to see if anything changed.
            event.apply(self)
            self._reapplyEvents()

        #TODO: Do we need this? Won't applying the new event cause this (or something more specific) to have been called already?
        self._notifyStateChangedListeners()

    def _reapplyEvents(self):
        """ reapply all uncertain events on top of the baseline.
            This should be the last thing which is done as part of adding an event as it may recurse into addEvent at the end.
        """
        self.pauseListeners = True
        oldGameState = self.currGameState
        self.currGameState = deepcopy(self.baselineGameState)
        newEvents = []
        for event in self.uncertainEvents:
            newEvent = event.apply(self)
            if newEvent:
                # We need to add a new event but we are in the middle of reapplying.
                # If this is a future event, it doesn't affect the reapply
                # If it is a past event, it will do its own re-applying so must be added once we are done.
                newEvents.append(newEvent)

        #un-pause listeners as we want to be told about changes due to these new events.
        self.pauseListeners = False

        # Check if any players stats might have been corrected as a result of this reapplying.
        # Send them a snapshot in case it has.

        # detect changes
        for oldPlayer in oldGameState.players.itervalues():
            newPlayer = self.getOrCreatePlayer(oldPlayer.teamID, oldPlayer.playerID)
            if (oldPlayer != newPlayer):
                print("Detected a Player in need of adjusting: ", oldPlayer, "->", newPlayer)
                snapshot = deepcopy(newPlayer)
                self._notifyPlayerAdjustedListeners(oldPlayer.teamID, oldPlayer.playerID, snapshot)

        #add the new events
        for newEvent in newEvents:
            self.addEvent(newEvent)

    def cancelEvent(self, predicate):
        "Cancel all uncertain and future events which match the given predicate"
        with self.stateLock:
            cancelledAnyUncertain = False
            for e in self.uncertainEvents[:]:
                if predicate(e):
                    self.uncertainEvents.remove(e)
                    # print("Cancelled: " + str(e))
                    cancelledAnyUncertain = True
            for e in self.futureEvents[:]:
                if predicate(e):
                    # print("Cancelled: " + str(e))
                    self.futureEvents.remove(e)
            if cancelledAnyUncertain:
                #we need to reapply the events now that some have been removed
                self._reapplyEvents()
            # print("New State: " + str(self.uncertainEvents) + " / " + str(self.futureEvents))

    # TODO: call this
    def adjustConfidencePoint(self, newConfidencePoint):
        with self.stateLock:
            if (newConfidencePoint < self.confidencePoint):
                raise RuntimeError("Tried to move the confidence point back in time")
            if (len(self.uncertainEvents) == 0):
                # Nothing to do
                self.confidencePoint = newConfidencePoint
            elif newConfidencePoint > self.uncertainEvents[len(self.uncertainEvents) - 1].serverTime:
                # new confidence point is later than all received events, just use the latest state as the baseline one.
                self.baselineGameState = deepcopy(self.currGameState)
                self.uncertainEvents = []
                self.confidencePoint = newConfidencePoint
            else:
                # new confidence point in the middle of our uncertain events. Rewind to our old confidence point, apply forward to our new confidence point and save that as baseline.
                self.pauseListeners = True
                latestGameState = self.currGameState
                self.currGameState = self.baselineGameState
                confidencePointIndex = 0
                for e in self.uncertainEvents:
                    if (e.serverTime > newConfidencePoint):
                        # too far into the future
                        break
                    else:
                        confidencePointIndex = confidencePointIndex + 1
                        e.apply(self)

                if confidencePointIndex > 0:
                    self.uncertainEvents = self.uncertainEvents[confidencePointIndex:]
                self.baselineGameState = self.currGameState
                # Now fast-forward to where we were when we started this calculation.
                self.currGameState = latestGameState
                self.confidencePoint = newConfidencePoint

                self.pauseListeners = False

    def addListener(self,
        currentStateChanged = None,
        playerAdjusted = None,
        playerMoved = None,
        gameStarted = None,
        gameStopped = None,
        fired = None
    ):
        """
        Add listeners which get notified about changes to gameState
        These won't get notified if a change happens just because we're reapplying past events.
        """
        if currentStateChanged:
            self.stateChangedListeners.append(currentStateChanged)
        if playerAdjusted:
            self.playerAdjustedListeners.append(playerAdjusted)
        if playerMoved:
            self.playerMovedListeners.append(playerMoved)
        if gameStarted:
            self.gameStartedListeners.append(gameStarted)
        if gameStopped:
            self.gameStoppedListeners.append(gameStopped)
        if fired:
            self.firedListeners.append(fired)

    def _notifyStateChangedListeners(self):
        if not self.pauseListeners:
            for l in self.stateChangedListeners:
                l()

    def _notifyPlayerAdjustedListeners(self, teamID, playerID, player):
        if not self.pauseListeners:
            for l in self.playerAdjustedListeners:
                l(teamID, playerID, player)

    def _notifyPlayerMovedListeners(self, oldTeamID, oldPlayerID, player):
        if not self.pauseListeners:
            for l in self.playerMovedListeners:
                l(oldTeamID, oldPlayerID, player)

    def _notifyGameStartedListeners(self):
        if not self.pauseListeners:
            for l in self.gameStartedListeners:
                l()

    def _notifyGameStoppedListeners(self):
        if not self.pauseListeners:
            for l in self.gameStoppedListeners:
                l()

    def notifyFiredListeners(self):
        if not self.pauseListeners:
            for l in self.firedListeners:
                l()