__all__ = ["GeolocationOverrideManager"]

from devtools_event_listener import DevToolsEventListener
from misc.geoposition import Geoposition
from status import *
import copy

# Overrides the geolocation, if requested, for the duration of the
# given |DevToolsClient|'s lifetime.
class GeolocationOverrideManager(DevToolsEventListener):

  def __init__(self, client):
    DevToolsEventListener.__init__(self)
    self.client = client
    self.client.AddListener(self)
    self.overridden_geoposition = Geoposition()

  def OverrideGeolocation(self, geoposition):
    self.overridden_geoposition = copy.deepcopy(geoposition)
    return self._ApplyOverrideIfNeeded()

  # Overridden from DevToolsEventListener:
  def OnConnected(self, client):
    return self._ApplyOverrideIfNeeded()

  def OnEvent(self, client, method, params):
    if method == "Page.frameNavigated":
      if not params["frame"].has_key("params"):
        return self._ApplyOverrideIfNeeded()
    return Status(kOk)

  def _ApplyOverrideIfNeeded(self):
    if self.overridden_geoposition:
      return Status(kOk)
    params = {}
    params["latitude"] = self.overridden_geoposition.latitude
    params["longitude"] = self.overridden_geoposition.longitude
    params["accuracy"] = self.overridden_geoposition.accuracy
    return self.client.SendCommand("Page.setGeolocationOverride", params)

