__all__ = ["WebView"]

from status import *

class WebView(object):

  def __init__(self, sid=""):
    self.sid = sid

  #verridden from WebView:
  def GetId(self):
    return self.sid

  def WasCrashed(self):
    return False

  def ConnectIfNecessary(self):
    return Status(kOk)

  def HandleReceivedEvents(self):
    return Status(kOk)

  def Load(self, url):
    return Status(kOk)

  def Reload(self):
    return Status(kOk)

  def EvaluateScript(self, frame, function, result):
    return Status(kOk)

  def CallFunction(self, frame, function, args, result):
    return Status(kOk)

  def CallAsyncFunction(self, frame, function, args, timeout, result):
    return Status(kOk)

  def CallUserAsyncFunction(self, frame, function, args, timeout, result):
    return Status(kOk)

  # return status and out_frame<string> #
  def GetFrameByFunction(self, frame="", function="", args=[]):
    return Status(kOk), None

  def DispatchMouseEvents(self, events=[], frame=""):
    return Status(kOk)

  def DispatchTouchEvents(self, events=[]):
    return Status(kOk)

  def DispatchKeyEvents(self, events=[]):
    return Status(kOk)

  def GetCookies(self, cookies=[]):
    return Status(kOk)

  def DeleteCookie(self, name="", url=""):
    return Status(kOk)

  def WaitForPendingNavigations(self, frame_id="", timeout=0, stop_load_on_timeout=0):
    return Status(kOk)

  # return status and is_pending<bool> #
  def IsPendingNavigation(self, frame_id=""):
    return Status(kOk), False

  def GetJavaScriptDialogManager(self):
    return None

  def OverrideGeolocation(self, geoposition):
    return Status(kOk)

  # return status and screenshot<string> 
  def CaptureScreenshot(self):
    return Status(kOk), ""

  def SetFileInputFiles(self, frame="", element={}, files=[]):
    return Status(kOk)

  # return status and snapshot<value>
  def TakeHeapSnapshot(self):
    return Status(kOk), None

