#!/usr/bin/python

import re
from datetime import date


class Event():
    """ An event is a message from a particular client (or the server if id == 0) at a particular time."""
    def __init__(self, msgStr, event_id, time):
        self.msgStr = msgStr
        self.id = event_id
        self.time = time

    def toStr(self):
        return "E(%x,%f,%s)" % (self.id, self.time, self.msgStr)

    def __str__(self):
        return "E(%x,%f(%s),%s)" % (self.id, self.time, date.fromtimestamp(self.time).isoformat(), self.msgStr)

    __repr__ = toStr


def parseEvent(line):
    regex = re.compile(r"^E\(([0-9a-f]+),([0-9.]+),(.*)\)$")
    m = regex.match(line)
    if not m:
        raise MessageParseException("Couldn't parse an event from '%s'" % line)
    (event_id, time, msgStr) = m.groups()
    return Event(msgStr, long(event_id, 16), float(time))


class MessageParseException(Exception):
    pass


class Message():
    """ A message, this is wrapped in an Event for client <-> server and sent raw from client <-> arduino."""
    def __init__(self, regex, subst):
        if regex is None:
            self.regex = None
        else:
            self.regex = re.compile("^" + regex + "$")
        self.subst = subst

    def parse(self, line, action=lambda: True):
        m = self.regex.match(line)
        if m:
            # Note that the number of groups in the regex must match the number of args which action takes
            # (and the default can only be used if there are no capture groups)
            actionResult = action(*m.groups())
            return actionResult or actionResult is None  # If the action doesn't return anything, assume all went well!
        else:
            return False

    def create(self, *args):
        if self.subst is None:
            raise RuntimeError("create is not supported for this message")
        return self.subst % args


class MessageHandler():
    def __init__(self):
        self.handlers = []

    def handles(self, msg):
        """A decorator which calls the decorated function if the given msg can be used to parse the given msgStr"""
        def handles_decorator(f):
            # defer a function to check if a msgStr parses and if so, invoke f and return True
            def handles_inner(msgStr):
                if msg.parse(msgStr, f):
                    return True
            self.handlers.append(handles_inner)

            # leave the function definition as-is even though it is practically useless now it has been used by the decorator.
            return f
        return handles_decorator

    def handle(self, msgStr):
        for handler in self.handlers:
            if handler(msgStr):
                return True
        return False


# both client <--> server
PING = Message(r"Ping\(\)", "Ping()")
PONG = Message(r"Pong\((\d*),(\d)\)", "Pong(%d,%s)")

# client -> server only
RECV = Message(r"Recv\((\d*),(\d*),(.*)\)", "Recv(%d,%d,%s)")
SENT = Message(r"Sent\((\d*),(\d*),(.*)\)", "Sent(%d,%d,%s)")
HELLO = Message(r"Hello\(\)", "Hello()")  # TODO: Add a protocol version check here

# server -> client only
STARTGAME = Message(r"StartGame\((\d*)\)", "StartGame(%d)")
STOPGAME = Message(r"StopGame\(\)", "StopGame()")
RESETGAME = Message(r"ResetGame\(\)", "ResetGame()")
DELETED = Message(r"Deleted\(\)", "Deleted()")
PLAYER_SNAPSHOT = Message(r"PlayerSnapshot\((.*)\)", "PlayerSnapshot(%s)")
PARAMETERS_SNAPSHOT = Message(r"ParametersSnapshot\((.*)\)", "ParametersSnapshot(%s)")
START_INITIALISING = Message(r"StartInitialising\(\)", "StartInitialising()")

# gun -> client (and usually also inside SENT and RECV for client -> server)
# NB. If we can create these, it is for the fakeGun
HIT =                 Message(r"H(\d),(\d),(\d)", "H%d,%d,%d")  # sentTeam, sentPlayer, damage
FULL_AMMO =           Message(r"FA", None)
CORRUPT =             Message(r"C", None)
CLIENT_CONNECTED =    Message(r"c", None)
CLIENT_DISCONNECTED = Message(r"d", None)
TRIGGER =             Message(r"T", "T")
TRIGGER_RELEASE =     Message(r"t", "t")
BATTERY =             Message(r"B(\d)", None)
INIT_HIT =            Message(r"InitHit", None)

# client -> gun
CLIENTCONNECT = Message(None, "c")
CLIENTDISCONNECT = Message(None, "d")
FIRE = Message(None, "Fire(%d,%d,%d)")
SHUTDOWN = Message(None, "Shutdown")
GUN_START_INITIALISING = Message(None, "Init")
GUN_FIRE_INITIALISING = Message(None, "FireInit")
GUN_STOP_INITIALISING = Message(None, "NoInit")
