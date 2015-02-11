__all__ = ["DebuggerTracker"]

from devtools_event_listener import DevToolsEventListener
from status import *

# Tracks the debugger state of the page.
class DebuggerTracker(DevToolsEventListener):

  def __init__(self, client):
    DevToolsEventListener.__init__(self)
    client.AddListener(self)

  # Overridden from DevToolsEventListener:
  def OnEvent(self, client, method, params):
    if method == "Debugger.paused":
      return client.SendCommand("Debugger.resume", {})
    return Status(kOk)

