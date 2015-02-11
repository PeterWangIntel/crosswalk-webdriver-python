__all__ = ["FrameTracker"]

from devtools_event_listener import DevToolsEventListener
from status import *
import json

# Tracks execution context creation.
class FrameTracker(DevToolsEventListener):

  def __init__(self, client):
    DevToolsEventListener.__init__(self)
    self.frame_to_context_map = {}
    client.AddListener(self)

  # return status and context_id<int>
  def GetContextIdForFrame(self, frame_id):
    context_id = self.frame_to_context_map.get(frame_id, None)
    if type(context_id) != int:
      return (Status(kNoSuchFrame, "context_id does not have frame"), -1)
    return (Status(kOk), context_id)

  # Overridden from DevToolsEventListener: 
  def OnConnected(self, client):
    self.frame_to_context_map.clear()
    params = {}
    status = client.SendCommand("Runtime.enable", params)
    if status.IsError():
      return status
    return client.SendCommand("Page.enable", params)

  def OnEvent(self, client, method, params):
    if method == "Runtime.executionContextCreated":
      context = params.get("context", None)
      if type(context) != dict:
        return Status(kUnknownError, "Runtime.executionContextCreated missing dict 'context'")
      context_id = context.get("id")
      frame_id = context.get("frameId")
      if type(context_id) != int or type(frame_id) != str:
        js = json.dumps(context)
        return Status(kUnknownError, "Runtime.executionContextCreated has invalid 'context': " + js)
      self.frame_to_context_map[frame_id] = context_id
    elif method == "Page.frameNavigated":
      if not params["frame"].has_key("parentId"):
        self.frame_to_context_map.clear() 
    return Status(kOk)

