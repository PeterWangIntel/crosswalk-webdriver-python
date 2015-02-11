__all__ = ["JavaScriptDialogManager"]

from devtools_event_listener import DevToolsEventListener
from status import *

# Tracks the opening and closing of JavaScript dialogs (e.g., alerts).
class JavaScriptDialogManager(DevToolsEventListener):
  
  def __init__(self, client):
    DevToolsEventListener.__init__(self)
    self.client = client
    self.client.AddListener(self)
    # The queue of unhandled dialogs. This may be greater than 1 in rare
    # cases. E.g., if the page shows an alert but before the manager received
    # the event, a script was injected via Inspector that triggered an alert.
    self.unhandled_dialog_queue = []
    
  def IsDialogOpen(self):
    return len(self.unhandled_dialog_queue) != 0

  # return status and message<string>
  def GetDialogMessage(self):
    if not self.IsDialogOpen():
      return (Status(kNoAlertOpen), "")
    message = self.unhandled_dialog_queue[0]
    return (Status(kOk), message)

  def HandleDialog(self, accept, text):
    if not self.IsDialogOpen():
      return Status(kNoAlertOpen)
    params = {}
    params["accept"] = accept
    if not text:
      params["promptText"] = text
    status = self.client.SendCommand("Page.handleJavaScriptDialog", params)
    if status.IsError():
      return status
    # Remove a dialog from the queue. Need to check the queue is not empty here,
    # because it could have been cleared during waiting for the command
    # response.
    if len(self.unhandled_dialog_queue):
      del self.unhandled_dialog_queue[0]
    return Status(kOk)

  # Overridden from DevToolsEventListener:
  def OnConnected(self, client):
    self.unhandled_dialog_queue = []
    params = {}
    return self.client.SendCommand("Page.enable", params)

  def OnEvent(self, client, method, params):
    if method == "Page.javascriptDialogOpening":
      message = params.get("message", None)
      if type(message) != str:
        return Status(kUnknownError, "dialog event missing or invalid 'message'")
      self.unhandled_dialog_queue.append(message)
    elif method == "Page.javascriptDialogClosing":
      # Inspector only sends this event when all dialogs have been closed.
      # Clear the unhandled queue in case the user closed a dialog manually.
      self.unhandled_dialog_queue = []
    return Status(kOk)

