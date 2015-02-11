__all__ = ["DevToolsClient"]

from status import *

""" A DevTools client of a single DevTools debugger. """
class DevToolsClient(object):

 def GetId(self):
   return "fake-id"

 def WasCrashed(self):
   return False
 
 def ConnectIfNecessary(self):
   """Connect to DevTools if the DevToolsClient is disconnected. """
   return Status(kOk)

 def SendCommand(self, method, params):
   return Status(kOk)

 def SendCommandAndGetResult(self, method, params, result):
   return Status(kOk)

 def AddListener(self, listener):
   """ Adds a listener. This must only be done when the client is disconnected.  """
   pass

 def HandleEventsUntil(self, conditional_func, timeout):
   """ Handles events until the given function reports the condition is met
       and there are no more received events to handle. If the given
       function ever returns an error, returns immediately with the error.
       If the condition is not met within |timeout|, kTimeout status
       is returned eventually. If |timeout| is 0, this function will not block. """
   return Status(kOk)
  
 def HandleReceivedEvents(self):
   """  Handles events that have been received but not yet handled. """
   return Status(kOk)

