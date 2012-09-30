#!/usr/bin/python

import argparse
import re
import socket

from core import Player, StandardGameLogic, ClientServer

class Main():

  def __init__(self):
    parser = argparse.ArgumentParser(description='BraidsTag gun logic.')
    parser.add_argument('-s', '--serial', type=argparse.FileType('r+'), help='serial device to which the arduino is connected', required=True)
    parser.add_argument('-p', '--playerID', type=stringToPlayerID, help='player id', default=1)
    parser.add_argument('-t', '--teamID', type=int, choices=xrange(1, 8), help='team id', default=1)

    self.args = parser.parse_args()

    self.player = Player(self.args.teamID, self.args.playerID)
    self.logic = StandardGameLogic()

  HIT_RE = re.compile(r"Shot\(Hit\((\d),(\d),(\d)\)\)")
  TRIGGER_RE = re.compile(r"Trigger\(\)")

  def eventLoop(self):
    for line in self.args.serial:
      line = line.rstrip()

      m = self.HIT_RE.match(line)
      if(m):
        (fromPlayer, fromTeam, damage) = m.groups()
        self.logic.hit(self.player, fromTeam, fromPlayer, damage)
      m = self.TRIGGER_RE.match(line)
      if(m):
        if (self.logic.trigger(self.player)):
          self.args.serial.write("Fire(%d,%d,%d)\n" % (self.player.teamID, self.player.playerID, self.player.gunDamage))

      msg = "Recv(%s,%s,%s)" % (self.player.teamID, self.player.playerID, line)
      self._sendToServer(msg, "Ack()")
      
  def _sendToServer(self, msg, ack = None):
    #send this packet to the server
    #TODO: should we do this asynchronously in a thread?
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ClientServer.SERVER, ClientServer.PORT))

    totalsent=0
    while totalsent < len(msg):
      sent = sock.send(msg[totalsent:])
      if sent == 0:
        #TODO handle this
        raise RuntimeError("socket connection broken")
      totalsent = totalsent + sent
    sock.shutdown(1);

    if ack:
      recieved = ''
      while len(recieved) < len(ack):
        chunk = sock.recv(len(ack)-len(recieved))
        if chunk == '':
          #TODO handle this
          raise RuntimeError("socket connection broken")
        recieved = recieved + chunk
      if recieved != ack:
        #TODO handle this
        raise RuntimeError("incorrect ack")

    #TODO: wait for the ACK.
    sock.close();
  
def stringToPlayerID(inp):
  out = int(inp)
  if out < 1 or out > 32:
    raise argparse.ArgumentTypeError("playerId must be between 1 and 32.")
  return out;


main = Main()
print main.player
main.eventLoop()
print main.player
main.args.serial.close()
