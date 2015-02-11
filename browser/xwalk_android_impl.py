__all__ = ["XwalkAndroidImpl"]

from xwalk_impl import XwalkImpl
from status import *

class XwalkAndroidImpl(XwalkImpl):
  def __init__(self, client, devtools_event_listeners, \
                port_reservation, device):
    XwalkImpl.__init__(self, client, \
                      devtools_event_listeners, port_reservation)
    self.device = device

  # Overridden from Xwalk
  def GetOperatingSystemName(self):
    return "ANDROID"

  # Overridden from XwalkImpl:
  def QuitImpl(self):
    return self.device.TearDown()

