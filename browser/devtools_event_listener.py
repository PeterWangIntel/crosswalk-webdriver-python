__all__ = ["DevToolsEventListener"]

from status import *

""" Receives notification of incoming Blink Inspector messages and connection
to the DevTools server. """

class DevToolsEventListener(object):

  def OnConnected(self, client):
    return Status(kOk)

  def OnEvent(self, client, method, params):
    return Status(kOk)

  def OnCommandSuccess(self, client, method):
    return Status(kOk)

