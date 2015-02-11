__all__ = ["PortReservation", \
           "PortManager", \
           "PortServer"]

import sys
import socket
import select
import os
import re
import random
from browser.status import *
from base.log import VLOG
from base.bind import Bind

class PortReservation(object):

  def __init__(self, on_free_func, port):
    self.on_free_func = on_free_func
    # port type: integer
    self.port = port

  def __del__(self):
    if callable(self.on_free_func):
      return self.on_free_func.Run()
    return

  def Leak(self):
    VLOG(0, "Port leaked: " + str(self.port))
    self.on_free_func = None
    return

class PortManager(object):

  def __init__(self, min_port, max_port):
    self.min_port = min_port
    self.max_port = max_port
    self.taken = []

  # return status and port<string> and reservation<PortReservation> 
  def ReservePort(self):
    start = random.randint(self.min_port, self.max_port)
    wrapped = False
    try_port = start
    while try_port != start or wrapped == False:
      if try_port > self.max_port:
        wrapped = True
        if self.min_port == self.max_port:
          break
        try_port = self.min_port
      if try_port in self.taken:
        try_port = try_port + 1
        continue
      sock = socket.socket()
      try:
        sock.bind(('localhost', try_port))
      except:
        try_port = try_port + 1
        continue
      self.taken.append(try_port)
      reservation = PortReservation(Bind(self.ReleasePort, [try_port]), try_port)
      #VLOG(0, "from port manager get try_port: " + str(try_port))
      return Status(kOk), str(try_port), reservation
    return Status(kUnknownError, "unable to find open port"), "", PortReservation(None, None)

  def ReleasePort(self, port):
    self.taken.remove(port)
    return

class PortServer(object):

  def __init__(self, path):
    if len(path) != 0 and path.startswith('\0'):
      self.path = path
      self,free = []
    else:
      VLOG(3, "path must be for Linux abstract namespace")

  # return status and a valid port<string>
  def RequestPort(self):
  # The client sends its PID + \n, and the server responds with a port + \n,
  # which is valid for the lifetime of the referred process.
    port = ""
    if 'linux2' != sys.platform:
      return Status(kUnknownError, "not implemented for this platform"), port
    try:
      sock_fd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
      sock_fd.setblocking(0)
    except:
      return Status(kUnknownError, "unable to create socket"), port
    try:
      sock_fd.settimeout(10)
    except:
      return Status(kUnknownError, "unable to set socket timeout"), port
    try:
      sock_fd.connect(self.path)
    except:
      return Status(kUnknownError, "unable to connect"), port
    try: 
      request = str(os.getpid()) + '\n'
      VLOG(0, "PORTSERVER REQUEST " + request)
      sock_fd.send(request)
      response = ""
      ready = select.select(sock_fd, None, None, 10)
      if ready:
        response = sock_fd.recv(1024)
      if not response:
        return Status(kUnknownError, "failed to receive portserver response"), port
      VLOG(0, "PORTSERVER RESPONSE " + response)
      # parse portserver response
      matchObj = re.search(r'([0-9]+)\n', response)
      if not matchObj:
        return Status(kUnknownError, "failed to parse portserver response"), port
      port = matchObj.groups()[0]
      return Status(kOk), port
    except socket.timeout:
      """ This exception is raised when a timeout occurs on a socket which has had timeouts 
      enabled via a prior call to settimeout(). The accompanying value is a string whose 
      value is currently always timed out """
      return Status(kUnknownError, "socket timeout"), port
    except:
      return Status(kUnknownError, "unable to send portserver request"), port
    
  def ReleasePort(self, port):
    self.free.append(port)
    return
   
  # return status and port<string> and reservation<PortReservation> 
  def ReservePort(self):
    port = ""
    port_reservation = PortReservation(None, None)
    if self.free:
      port = self.free[0]
      del self.free[0]
    status, port = self.RequestPort()
    if status.IsError():
      return status, port, port_reservation
    port_reservation = PortReservation(Bind(self.ReleasePort, [port]), port)
    return status, port, port_reservation

