__all__ = ["NavigationTracker"]

from status import *
from devtools_event_listener import DevToolsEventListener

# Tracks the navigation state of the page.
class NavigationTracker(DevToolsEventListener):

  kUnknown = 0
  kLoading = 1
  kNotLoading = 2

  def __init__(self, client, known_state=0):
    self.client = client
    self.client.AddListener(self)
    self.loading_state = known_state
    self.scheduled_frame_set = set()

  # return status and is_pending<bool> 
  def IsPendingNavigation(self, frame_id):
    # Gets whether a navigation is pending for the specified frame. |frame_id|
    # may be empty to signify the main frame.
    if self.loading_state == NavigationTracker.kUnknown:
      # If the loading state is unknown (which happens after first connecting),
      # force loading to start and set the state to loading. This will
      # cause a frame start event to be received, and the frame stop event
      # will not be received until all frames are loaded.
      # Loading is forced to start by attaching a temporary iframe.
      # Forcing loading to start is not necessary if the main frame is not yet
      # loaded.
      kStartLoadingIfMainFrameNotLoading = \
          "var isLoaded = document.readyState == 'complete' ||"\
          "    document.readyState == 'interactive';"\
          "if (isLoaded) {"\
          "  var frame = document.createElement('iframe');"\
          "  frame.src = 'about:blank';"\
          "  document.body.appendChild(frame);"\
          "  window.setTimeout(function() {"\
          "    document.body.removeChild(frame);"\
          "  }, 0);"\
          "}"
      params = {} 
      params["expression"] = kStartLoadingIfMainFrameNotLoading
      result = {}
      status = self.client.SendCommandAndGetResult("Runtime.evaluate", params, result)
      if status.IsError():
        return (Status(kUnknownError, "cannot determine loading status"), False)
      # Between the time the JavaScript is evaluated and SendCommandAndGetResult
      # returns, OnEvent may have received info about the loading state.
      # This is only possible during a nested command. Only set the loading state
      # if the loading state is still unknown.

      if self.loading_state == NavigationTracker.kUnknown:
        self.loading_state = NavigationTracker.kLoading
    is_pending = (self.loading_state == NavigationTracker.kLoading)
    if not frame_id:
      is_pending |= (len(self.scheduled_frame_set) > 0)
    else:
      is_pending |= (frame_id in self.scheduled_frame_set)
    return (Status(kOk), is_pending)

  def OnConnected(self, client):
    self.loading_state = NavigationTracker.kUnknown
    self.scheduled_frame_set = set()
    # Enable page domain notifications to allow tracking navigating state
    return self.client.SendCommand("Page.enable", {})

  def OnEvent(self, client, method, params):
    # Xwalk does not send Page.frameStoppedLoading until all frames have
    # run their onLoad handlers (including frames created during the handlers).
    # When it does, it only sends one stopped event for all frames.
    if method == "Page.frameStartedLoading":
      self.loading_state = NavigationTracker.kLoading
    elif method == "Page.frameStoppedLoading":
      self.loading_state = NavigationTracker.kNotLoading
    elif method == "Page.frameScheduledNavigation":
      delay = params.get("delay", None)
      if delay == None:
        return Status(kUnknownError, "missing or invalid 'delay'")
      frame_id = params.get("frameId", None)
      if type(frame_id) != str:
        return Status(kUnknownError, "missing or invalid 'frameId'")
      # WebDriver spec says to ignore redirects over 1s.
      if delay > 1.0:
        return Status(kOk)
      self.scheduled_frame_set.add(frame_id)
    elif method == "Page.frameClearedScheduledNavigation":
      frame_id = params.get("frameId", None)
      if type(frame_id) != str:
        return Status(kUnknownError, "missing or invalid 'frameId'")
      self.scheduled_frame_set.remove(frame_id)
    elif method == "Page.frameNavigated":
      # Note: in some cases Page.frameNavigated may be received for subframes
      # without a frameStoppedLoading (for example cnn.com).

      # If the main frame just navigated, discard any pending scheduled
      # navigations. For some reasons at times the cleared event is not
      # received when navigating.
      # See crbug.com/180742.
      if not params["frame"].has_key("parentId"):
        self.scheduled_frame_set = set()
    elif method == "Inspector.targetCrashed":
      self.loading_state = NavigationTracker.kNotLoading
      self.scheduled_frame_set = set()
    return Status(kOk)

  def OnCommandSuccess(self, client, method):
    if method == "Page.navigate" and self.loading_state != NavigationTracker.kLoading:
      # At this point the browser has initiated the navigation, but besides that,
      # it is unknown what will happen.
      #
      # There are a few cases (perhaps more):
      # 1 The RenderViewHost has already queued ViewMsg_Navigate and loading
      #   will start shortly.
      # 2 The RenderViewHost has already queued ViewMsg_Navigate and loading
      #   will never start because it is just an in-page fragment navigation.
      # 3 The RenderViewHost is suspended and hasn't queued ViewMsg_Navigate
      #   yet. This happens for cross-site navigations. The RenderViewHost
      #   will not queue ViewMsg_Navigate until it is ready to unload the
      #   previous page (after running unload handlers and such).
      #
      # To determine whether a load is expected, do a round trip to the
      # renderer to ask what the URL is.
      # If case #1, by the time the command returns, the frame started to load
      # event will also have been received, since the DevTools command will
      # be queued behind ViewMsg_Navigate.
      # If case #2, by the time the command returns, the navigation will
      # have already happened, although no frame start/stop events will have
      # been received.
      # If case #3, the URL will be blank if the navigation hasn't been started
      # yet. In that case, expect a load to happen in the future.
      self.loading_state = NavigationTracker.kUnknown
      params = {}
      params["expression"] = "document.URL"
      result = {}
      status = self.client.SendCommandAndGetResult("Runtime.evaluate", params, result)
      url = result["result"].get("value", None)
      if status.IsError() or type(url) != str:
        return Status(kUnknownError, "cannot determine loading status", status)
      if self.loading_state == NavigationTracker.kUnknown and not url:
        self.loading_state = NavigationTracker.kLoading
    return Status(kOk)
 
