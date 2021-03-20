from __future__ import print_function

import socket
import sys
import time
from threading import Thread, Lock
import Queue

from proto import Event, PING


class PiSerialIdProvider():
    """ An IdProvider which uses the serial number of the CPU (i.e. of the Pi) or, failing that, a random number"""
    def __init__(self):
        self.clientId = None

        # Try to extract serial from cpuinfo file
        try:
            f = open('/proc/cpuinfo', 'r')
            for line in f:
                if line[0:6] == 'Serial':
                    self.clientId = long(line[10:26], 16)
                    print("Found client Id from CPU serial number: ", self.clientId)
            f.close()
        except:
            pass

        # Fallback to a random number
        if not self.clientId:
            import random
            self.clientId = random.getrandbits(64)
            print("Falling back to a random client Id (instead of CPU serial number): ", self.clientId)

    def __call__(self):
        return self.clientId


class ClientServerConnection(object):
    def __init__(self, idProvider=PiSerialIdProvider()):
        self.sock = None
        self.readThread = None
        self.writeThread = WriteThread(idProvider)
        self.writeThread.start()

    def queueMessage(self, msg):
        print("-->", repr(msg))
        sys.stdout.flush()

        self.writeThread.queueMessage(msg)

    def setSocket(self, sock):
        self.sock = sock

        # clean up old thread
        if self.readThread:
            self.readThread.stop()

        # start new one
        self.readThread = ReadThread(self.sock, self)
        self.readThread.start()

        self.writeThread.setSocket(self.sock)

    def _closeConnection(self):
        if self.sock:
            self.sock.shutdown(2)
            self.sock.close()
            self.sock = None

    def onDisconnect(self):
        """Called when this connection is disconnected. Should be overridden in subclasses"""
        raise RuntimeError("onDisconnectCalled")

    def stop(self):
        self.writeThread.stop()
        self.readThread.stop()
        self._closeConnection()

    def startLatencyCheck(self):
        self.queueMessage(PING.create())


class ReadThread(Thread):
    def __init__(self, sock, parent):
        super(ReadThread, self).__init__(group=None)
        self.setDaemon(True)
        self.name = "Client/Server Read Thread"
        self.sock = sock
        self.parent = parent
        self.shouldStop = False

    def run(self):
        received = ''
        while True:
            try:
                chunk = self.sock.recv(1024)
            except socket.timeout:
                if self.shouldStop:
                    # this is expected
                    return
                continue
            except socket.error:
                if self.shouldStop:
                    # this is expected
                    return
                self.parent.onDisconnect()
                break
            if chunk == '':
                if self.shouldStop:
                    # this is expected
                    return
                self.parent.onDisconnect()
                break
            received = received + chunk

            (partial, complete) = self._takeCompleteResponses(received)
            received = partial

            for i in complete:
                print("<--", repr(i))
                sys.stdout.flush()

                if self.parent.handleMsg(i):
                    continue
                else:
                    raise RuntimeError("Received unknown message: %s" % i)

    @staticmethod
    def _takeCompleteResponses(received):
        """Extract complete responses from a char stream.
           return a tuple containing the remaining partial response and a list of complete responses
        """
        allResp = received.split('\n')
        partial = allResp.pop(-1)

        return partial, allResp

    def stop(self):
        self.shouldStop = True


class WriteThread(Thread):
    def __init__(self, idProvider):
        super(WriteThread, self).__init__(group=None)
        self.setDaemon(True)
        self.name = "Client/Server Write Thread"
        self.sock = None  # this will be set by setSocket
        self.queue = Queue.Queue()
        self.shouldStop = False

        self.idProvider = idProvider

    def run(self):
        while not self.shouldStop:
            try:
                msg = self.queue.get(True, 5).toStr() + "\n"
            except Queue.Empty:
                # timeout, go back round the loop to see if we should be stopping.
                continue
            try:
                totalsent = 0
                while totalsent < len(msg):
                    sent = self.sock.send(msg[totalsent:])
                    if sent == 0:
                        # NB. we should rely on the readThread to signal a closed connection
                        # TODO handle this
                        raise RuntimeError("socket connection broken")
                    totalsent = totalsent + sent
            except:
                print("Unexpected error:", sys.exc_info()[0])
                raise
                # TODO retry sending the packet
        print ("Write Thread exiting")

    def stop(self):
        """shut the client server connection down nicely. This blocks until shutdown is finished."""
        self.shouldStop = True
        self.join()

    def queueMessage(self, msg):
        self.queue.put(Event(msg, self.idProvider(), time.time()))

    def setSocket(self, sock):
        self.sock = sock
