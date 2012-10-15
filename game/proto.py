#!/usr/bin/python

import re

class Message():
  def __init__(self, regex):
    self.regex = re.compile(regex)

  def parse(self, line):
    m = self.regex.match(line)
    if(m):
      return m.groups()
    else:
      raise MessageParseException()

  def create(self, args):
    pass

class MessageParseException(Exception):
  pass

# both client <--> server

#client -> server only
RECV = Message(r"Recv\((\d*),(\d*),(.*)\)")
SENT = Message(r"Sent\((\d*),(\d*),(.*)\)")
HELLO = Message(r"Hello\((-?\d*),(-?\d*)\)")

#server -> client only
TRIGGER = Message(r"Trigger\(\)")
TEAMPLAYER = Message(r"TeamPlayer\((\d),(\d+)\)")

#gun -> client (and inside SENT and REV)
HIT = Message(r"Shot\(Hit\((\d),(\d),(\d)\)\)")
