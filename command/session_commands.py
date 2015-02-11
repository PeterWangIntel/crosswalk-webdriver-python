__all__ = ["ExecuteGetSessionCapabilities", \
           "ExecuteImplicitlyWait", \
           "ExecuteSetTimeout", \
           "ExecuteSetScriptTimeout", \
           "ExecuteGetCurrentWindowHandle", \
           "ExecuteIsLoading", \
           "ExecuteGetBrowserOrientation", \
           "ExecuteGetLocation", \
           "ExecuteGetAppCacheStatus", \
           "ExecuteGetWindowHandles", \
           "ExecuteClose", \
           "ExecuteSwitchToWindow"]

from browser.status import *
from browser.web_view_impl import WebViewImpl
from base.log import VLOG
from misc.basic_types import WebPoint

kWindowHandlePrefix = "CDwindow-"

def _WebViewIdToWindowHandle(web_view_id):
  return kWindowHandlePrefix + web_view_id

# return bool and web_view_id<string>
def _WindowHandleToWebViewId(window_handle):
  if kWindowHandlePrefix in window_handle:
    return (True, window_handle[len(kWindowHandlePrefix):])
  return (False, "")

def ExecuteSessionCommand(command, session, params, value):
  command.Update([session, params, value])
  status = command.Run()
  
  if status.IsError() and session.xwalk:
    if not session.quit and session.xwalk.HasCrashedWebView():
      session.quit = True
      message = "session deleted because of page crash"
      if not session.detach:
        quit_status = session.xwalk.Quit()
        if quit_status.IsError():
          message += ", but failed to kill browser:" + quit_status.Message()
      status = Status(kUnknownError, message)
    elif status.Code() == kDisconnected:
      # Some commands, like clicking a button or link which closes the window,
      # may result in a kDisconnected error code.
      web_view_ids = []
      status_tmp = session.xwalk.GetWebViewIds(web_view_ids)
      if status_tmp.IsError() and status_tmp.Code() != kXwalkNotReachable:
        status.AddDetails("failed to check if window was closed: " + status_tmp.Message())
      elif session.window not in web_view_ids:
        status = Status(kOk) 
    if status.IsError():
      status.AddDetails("Session info: xwalk=" + session.xwalk.GetVersion())
  return status

def ExecuteGetSessionCapabilities(session, params, value):
  value.clear()
  value.update(session.capabilities)
  return Status(kOk)

def ExecuteImplicitlyWait(session, params, value):
  ms = params.get("ms", -1.0)
  if type(ms) != float or ms < 0.0:
    return Status(kUnknownError, "'ms' must be a non-negative number")
  session.implicit_wait = int(ms)
  return Status(kOk)

def ExecuteSetTimeout(session, params, value):
  ms_double = params.get("ms")
  if type(ms_double) != float:
    return Status(kUnknownError, "'ms' must be a double")
  typer = params.get("type")
  if type(typer) != str:
    return Status(kUnknownError, "'type' must be a string")
  timeout = int(ms_double)
  # TODO(wyh): implicit and script timeout should be cleared
  # if negative timeout is specified.
  if typer == "implicit":
    session.implicit_wait = timeout
  elif typer == "script":
    session.script_timeout = timeout
  elif typer == "page load":
    session.page_load_timeout = session.kDefaultPageLoadTimeout if timeout < 0 else timeout
  else:
    return Status(kUnknownError, "unknown type of timeout:" + typer)
  return Status(kOk)

def ExecuteSetScriptTimeout(session, params, value):
  ms = params.get("ms", -1.0)
  if type(ms) != float or ms < 0.0:
    return Status(kUnknownError, "'ms' must be a non-negative number")
  session.script_timeout = int(ms)
  return Status(kOk)

def ExecuteGetCurrentWindowHandle(session, params, value):
  web_view = WebViewImpl("fake", 0, None)
  status = session.GetTargetWindow(web_view)
  web_view_ids = []
  if status.IsError():
    return status
  value.clear()
  value.update({"value": _WebViewIdToWindowHandle(session.window)})
  return Status(kOk)

def ExecuteIsLoading(session, params, value):
  web_view = WebViewImpl("fake", 0, None)
  status = session.GetTargetWindow(web_view)
  if status.IsError():
    return status

  status = web_view.ConnectIfNecessary()
  if status.IsError():
    return status

  is_pending = False
  (status, is_pending) = web_view.IsPendingNavigation(session.GetCurrentFrameId())
  if status.IsError():
    return status
  value.clear()
  value.update({"value": is_pending})
  return Status(kOk)

def ExecuteGetBrowserOrientation(session, params, value):
  web_view = WebViewImpl("fake", 0, None)
  status = session.GetTargetWindow(web_view)
  if status.IsError():
    return status

  status = web_view.ConnectIfNecessary()
  if status.IsError():
    return status

  kGetBrowserOrientationScript = "function() { return window.screen.orientation;}"
  result = {}
  status = web_view.CallFunction(session.GetCurrentFrameId(), kGetBrowserOrientationScript, [], result)
  if status.IsError():
    return status
  orientation = result["value"].get("type")
  if type(orientation) != str:
    return status(kUnknownError, "Failed acquire current browser's orientation")
  
  value.clear()
  value.update({"value": orientation})
  return Status(kOk)

def ExecuteGetLocation(session, params, value):
  if not session.overridden_geoposition:
    return Status(kUnknownError, "Location must be set before it can be retrieved")
  location = {}
  location["latitude"] = session.overridden_geoposition.latitude
  location["longitude"] = session.overridden_geoposition.longitude
  location["accuracy"] = session.overridden_geoposition.accuracy
  # Set a dummy altitude to make WebDriver clients happy.
  # https://code.google.com/p/chromedriver/issues/detail?id=281
  location["altitude"] = 0.0
  value.clear()
  value.update(location)
  return Status(kOk)

def ExecuteGetAppCacheStatus(session, params, value):
  web_view = WebViewImpl("fake", 0, None)
  status = session.GetTargetWindow(web_view)
  if status.IsError():
    return status

  status = web_view.ConnectIfNecessary()
  if status.IsError():
    return status

  kGetAppCacheStatus = "function() { return window.applicationCache.status;}"
  result = {}
  status = web_view.CallFunction(session.GetCurrentFrameId(), kGetAppCacheStatus, [], result)
  if status.IsError():
    return status
  cache_status = result["value"]
  if type(cache_status) != int:
    return status(kUnknownError, "Failed acquire current application cache status")
  
  value.clear()
  value.update({"value": cache_status})
  return Status(kOk)

def ExecuteGetWindowHandles(session, params, value):
  web_view_ids = []
  status = session.xwalk.GetWebViewIds(web_view_ids)
  if status.IsError():
    return status
  window_ids = []
  for it in web_view_ids:
    window_ids.append(_WebViewIdToWindowHandle(it))

  value.clear()
  value.update({"value": window_ids})
  return Status(kOk)

def ExecuteClose(session, params, value):
  web_view_ids = []
  status = session.xwalk.GetWebViewIds(web_view_ids)
  if status.IsError():
    return status
  is_last_web_view = (len(web_view_ids) == 1)
  web_view_ids = []

  web_view = WebViewImpl("fake", 0, None)
  status = session.GetTargetWindow(web_view)
  if status.IsError():
    return status

  status = session.xwalk.CloseWebView(web_view.GetId())
  if status.IsError():
    return status

  status = session.xwalk.GetWebViewIds(web_view_ids)

  if ((status.Code() == kXwalkNotReachable and is_last_web_view) or \
    (status.IsOk() and len(web_view_ids) == 1)):
    # when the last web_view_id is "WebViewImpl("fake", 0, None)"
    # If no window is open, close is the equivalent of calling "quit".
    session.quit = True;
    return session.xwalk.Quit()
  return status;

def ExecuteSwitchToWindow(session, params, value):
  name = params.get("name")
  if type(name) != str:
    return Status(kUnknownError, "'name' must be a nonempty string")

  web_view_ids = []
  status = session.xwalk.GetWebViewIds(web_view_ids)
  if status.IsError():
    return status

  web_view_id = ""
  found = False
  (flag, web_view_id) = _WindowHandleToWebViewId(name)
  if flag and web_view_id in web_view_ids:
    # Check if any web_view matches |web_view_id|.
      found = True
  else:
    # Check if any of the tab window names match |name|.
    kGetWindowNameScript = "function() { return window.name; }"
    for it in web_view_ids:
      result = {}
      web_view = WebViewImpl("fake", 0, None)
      status = session.xwalk.GetWebViewById(it, web_view)
      if status.IsError():
        return status
      status = web_view.ConnectIfNecessary()
      if status.IsError():
        return status
      status = web_view.CallFunction("", kGetWindowNameScript, [], result)
      if status.IsError():
        return status
      window_name = result["value"]
      if type(window_name) != str:
        return Status(kUnknownError, "failed to get window name")
      if window_name == name:
        web_view_id = it
        found = True
        break

  if not found:
    return Status(kNoSuchWindow)

  if session.overridden_geoposition:
    web_view = WebViewImpl("fake", 0, None)
    status = session.xwalk.GetWebViewById(web_view_id, web_view)
    if status.IsError():
      return status
    status = web_view.ConnectIfNecessary()
    if status.IsError():
      return status
    status = web_view.OverrideGeolocation(session.overridden_geoposition)
    if status.IsError():
      return status

  session.window = web_view_id
  session.SwitchToTopFrame()
  session.mouse_position = WebPoint(0, 0)
  return Status(kOk)


