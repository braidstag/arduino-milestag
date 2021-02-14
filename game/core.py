#!/usr/bin/python

from __future__ import print_function

import os

class ClientServer():
  PORT=int(os.getenv("PORT", "7079"))
  APIPORT=int(os.getenv("APIPORT", "8080"))
  SERVER=os.getenv("SERVER", "192.168.1.151")


class ArgumentError(Exception):
  pass