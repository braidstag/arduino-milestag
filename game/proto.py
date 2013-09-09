#!/usr/bin/python

import re

class Event():
  """ An event is a message from a particular client (or the server if id == 0) at a particular time."""
  def __init__(self, msgStr, id, time):
    self.msgStr = msgStr
    self.id = id
    self.time = time

  def toStr(self):
    return "E(%x,%f,%s)" % (self.id, self.time, self.msgStr)


def parseEvent(line):
  regex = re.compile("^E\(([0-9a-f]+),([0-9.]+),(.*)\)$")
  m = regex.match(line)
  if(not m):
    raise MessageParseException("Couldn't parse an event from '%s'" % line)
  (id, time, msgStr) = m.groups()
  return Event(msgStr, int(id), float(time))


class Message():
  """ A message, this is wrapped in an Event for client <-> server and sent raw from client <-> arduino."""
  def __init__(self, regex, subst):
    if regex == None:
      self.regex = None
    else:
      self.regex = re.compile("^" + regex + "$")
    self.subst = subst

  def parse(self, line):
    m = self.regex.match(line)
    if(m):
      return m.groups()
    else:
      raise MessageParseException()

  def create(self, *args):
    if self.subst == None:
      raise RuntimeError("create is not supported for this message")
    return self.subst % args


class MessageParseException(Exception):
  pass

# both client <--> server

#client -> server only
RECV = Message(r"Recv\((\d*),(\d*),(.*)\)", "Recv(%d,%d,%s)")
SENT = Message(r"Sent\((\d*),(\d*),(.*)\)", "Sent(%d,%d,%s)")
HELLO = Message(r"Hello\((-?\d*),(-?\d*)\)", "Hello(%d,%d)")
#server -> client only
TEAMPLAYER = Message(r"TeamPlayer\((\d),(\d+)\)", "TeamPlayer(%d,%d)")
STARTGAME = Message(r"StartGame\((\d*)\)", "StartGame(%d)")
STOPGAME = Message(r"StopGame\(\)", "StopGame()")
RESETGAME = Message(r"ResetGame\(\)", "ResetGame()")

DELETED = Message(r"Deleted\(\)", "Deleted()")

#gun -> client (and usually also inside SENT and RECV for client -> server)
HIT =                 Message(r"H(\d),(\d),(\d)", None)
FULL_AMMO =           Message(r"FA", None)
CORRUPT =             Message(r"C", None)
CLIENT_CONNECTED =    Message(r"c", None)
CLIENT_DISCONNECTED = Message(r"d", None)
TRIGGER =             Message(r"T", None)
TRIGGER_RELEASE =     Message(r"t", None)
BATTERY =             Message(r"B(\d)", None)

#client -> gun
CLIENTCONNECT = Message(None, "c")
CLIENTDISCONNECT = Message(None, "d")
FIRE = Message(None, "Fire(%d,%d,%d)")

