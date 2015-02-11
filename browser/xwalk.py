__all__ = ["Xwalk"]

from status import *
from version import GetMinimumSupportedXwalkVersion

class Xwalk(object):

  def GetAsDesktop(self):
    return None

  def GetVersion(self):
    return GetMinimumSupportedXwalkVersion()

  def GetBuildNo(self):
    return 9999

  def HasCrashedWebView(self):
    return False

  # Return ids of opened WebViews in the same order as they are opened.
  def GetWebViewIds(self, web_view_ids): 
    return Status(kOk)

  # Return WebView for the given id.
  def GetWebViewById(self, sid, web_view):
    return Status(kOk)

  # Closes the specified WebView.
  def CloseWebView(self, sid):
    return Status(kOk)

  # Activates the specified WebView.
  def ActivateWebView(self, sid):
    return Status(kOk)

  # Get the operation system where Xwalk is running.
  def GetOperatingSystemName(self):
    return "ANDROID"

  # Quits Xwalk.
  def Quit(self):
    return Status(kOk)

if __name__ == "__main__":
  test = Xwalk()
  print test.GetOperatingSystemName()
  print test.GetBuildNo()

