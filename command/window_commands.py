__all__ = ["ExecuteWindowCommand", \
           "ExecuteGetTitle", \
           "ExecuteRefresh", \
           "ExecuteGetCurrentUrl", \
           "ExecuteGetPageSource", \
           "ExecuteIsBrowserOnline", \
           "ExecuteGet", \
           "ExecuteGoBack", \
           "ExecuteGoForward", \
           "ExecuteFindElement", \
           "ExecuteFindElements", \
           "ExecuteExecuteScript", \
           "ExecuteExecuteAsyncScript", \
           "ExecuteScreenshot", \
           "ExecuteGetWindowSize", \
           "ExecuteGetWindowPosition", \
           "ExecuteGetCookies", \
           "ExecuteAddCookie", \
           "ExecuteDeleteCookie", \
           "ExecuteDeleteAllCookies", \
           "ExecuteSwitchToFrame"]

from browser.status import *
from browser.js import *
from browser.web_view_impl import WebViewImpl
from base.log import VLOG
from command.element_util import FindElement
from command.init_session_commands import GenerateId

class Cookie(object):
  
  def __init__(self, name, value, domain, path, expiry, secure, session):
    self.name = name
    self.value = value
    self.domain = domain
    self.path = path
    self.expiry = expiry
    self.secure = secure
    self.session = session

  def Update(self, other):
    self.name = other.name
    self.value = other.value
    self.domain = other.domain
    self.path = other.path
    self.expiry = other.expiry
    self.secure = other.secure
    self.session = other.session

def _CreateDictionaryFrom(cookie):
  dictionary = {}
  dictionary["name"] = cookie.name
  dictionary["value"] = cookie.value
  if cookie.domain:
    dictionary["domain"] = cookie.domain
  if cookie.path:
    dictionary["path"] = cookie.path
  if not cookie.session:
    dictionary["expiry"] = cookie.expiry
  dictionary["secure"] = cookie.secure
  return dictionary

def _GetVisibleCookies(web_view, cookies):
  internal_cookies = []
  status = web_view.GetCookies(internal_cookies)
  if status.IsError():
    return status

  cookies_tmp = []
  for cookie_dict in internal_cookies:
    if type(cookie_dict) != dict:
      return Status(kUnknownError, "DevTools returns a non-dictionary cookie")
    name = cookie_dict.get("name", "")
    value = cookie_dict.get("value", "")
    domain = cookie_dict.get("domain", "")
    path = cookie_dict.get("path", "")
    expiry = cookie_dict.get("expires", 0)
    # Convert from millisecond to second.
    expiry = expiry / 1000.0  
    session = cookie_dict.get("session", False)
    secure = cookie_dict.get("secure", False)
    cookies_tmp.append(Cookie(name, value, domain, path, expiry, secure, session))
 
  cookies[:] = cookies_tmp
  return Status(kOk)

# return status and url<string>
def _GetUrl(web_view, frame):
  value = {}
  args = []
  status = web_view.CallFunction(frame, "function() { return document.URL; }", args, value)
  if status.IsError():
    return (status, "")
  if type(value["value"]) != str:
    return (Status(kUnknownError, "javascript failed to return the url"), "")
  return (Status(kOk), value["value"])

def ExecuteWindowCommand(command, session, params, value):
  web_view = WebViewImpl("fake_id", 0, None)
  # update web_view
  status = session.GetTargetWindow(web_view)
  if status.IsError():
    return status

  status = web_view.ConnectIfNecessary()
  if status.IsError():
    return status

  status = web_view.HandleReceivedEvents()
  if status.IsError():
    return status

  if web_view.GetJavaScriptDialogManager().IsDialogOpen():
    return Status(kUnexpectedAlertOpen)

  nav_status = Status(kOk)
  for attempt in range(2):
    if attempt == 1:
      if status.Code() == kNoSuchExecutionContext:
        # Switch to main frame and retry command if subframe no longer exists.
        session.SwitchToTopFrame()
      else:
        break
    nav_status = web_view.WaitForPendingNavigations(session.GetCurrentFrameId(), session.page_load_timeout, True)
    if nav_status.IsError():
      return nav_status
    command.Update([session, web_view, params, value])
    status = command.Run()
  nav_status = web_view.WaitForPendingNavigations(session.GetCurrentFrameId(), session.page_load_timeout, True)

  if status.IsOk() and nav_status.IsError() and nav_status.Code() != kUnexpectedAlertOpen:
    return nav_status
  if status.Code() == kUnexpectedAlertOpen:
    return Status(kOk)
  return status

def ExecuteGetTitle(session, web_view, params, value):
  kGetTitleScript = "function() {"\
                    "  if (document.title)"\
                    "    return document.title;"\
                    "  else"\
                    "    return document.URL;"\
                    "}"
  args = []
  return web_view.CallFunction("", kGetTitleScript, args, value)

def ExecuteRefresh(session, web_view, params, value):
  return web_view.Reload()

def ExecuteGetCurrentUrl(session, web_view, params, value):
  (status, url) = _GetUrl(web_view, session.GetCurrentFrameId())
  if status.IsError():
    return status
  value.clear()
  value.update(url)   
  return Status(kOk)

def ExecuteGetPageSource(session, web_view, params, value):
  kGetPageSource = \
      "function() {"\
      "  return new XMLSerializer().serializeToString(document);"\
      "}"
  return web_view.CallFunction(session.GetCurrentFrameId(), kGetPageSource, [], value)

def ExecuteIsBrowserOnline(session, web_view, params, value):
  return web_view.EvaluateScript(session.GetCurrentFrameId(), "navigator.onLine", value)

def ExecuteGet(session, web_view, params, value):
  url = params.get("url", None)
  if type(url) != str:
    return Status(kUnknownError, "'url' must be a string")
  return web_view.Load(url)

def ExecuteGoBack(session, web_view, params, value):
  return web_view.EvaluateScript("", "window.history.back();", value)

def ExecuteGoForward(session, web_view, params, value):
  return web_view.EvaluateScript("", "window.history.forward();", value)

def ExecuteFindElement(session, web_view, params, value):
  interval_ms = 50
  return FindElement(interval_ms, True, "", session, web_view, params, value)

def ExecuteFindElements(session, web_view, params, value):
  interval_ms = 50
  return FindElement(interval_ms, False, "", session, web_view, params, value)

def ExecuteExecuteScript(session, web_view, params, value):
  script = params.get("script")
  if type(script) != str:
    return Status(kUnknownError, "'script' must be a string")
  if script == ":takeHeapSnapshot":
    #TODO:
    #return web_view->TakeHeapSnapshot(value);
    pass
  else:
    args = params.get("args")
    if type(args) != list:
      return Status(kUnknownError, "'args' must be a list")
    return web_view.CallFunction(session.GetCurrentFrameId(), "function(){" + script + "}", args, value)

def ExecuteExecuteAsyncScript(session, web_view, params, value):
  script = params.get("script")
  if type(script) != str:
    return Status(kUnknownError, "'script' must be a string")
  args = params.get("args")
  if type(args) != list:
    return Status(kUnknownError, "'args' must be a list")
  return web_view.CallUserAsyncFunction(session.GetCurrentFrameId(), "function(){" + script + "}", args, session.script_timeout, value)

def ExecuteScreenshot(session, web_view, params, value):
  status = session.xwalk.ActivateWebView(web_view.GetId())

  (status, screenshot) = web_view.CaptureScreenshot()
  if status.IsError():
    return status
  
  value.clear()
  value.update({"value": screenshot})
  return Status(kOk)

def ExecuteGetWindowSize(session, web_view, params, value):
  result = {}
  kExecuteGetWindowSizeScript = \
      "function() {"\
      "  var size = {'height': 0, 'width': 0};"\
      "  size.height = window.screen.height;"\
      "  size.width = window.screen.width;"\
      "  return size;"\
      "}"
  status = web_view.CallFunction(session.GetCurrentFrameId(), \
               kExecuteGetWindowSizeScript, [], result)
  if status.IsError():
    return status

  value.clear()
  value.update(result)
  return Status(kOk)

def ExecuteGetWindowPosition(session, web_view, params, value):
  result = {}
  kGetWindowPositionScript = \
      "function() {"\
      "  var position = {'x': 0, 'y': 0};"\
      "  position.x = window.screenX;"\
      "  position.y = window.screenY;"\
      "  return position;"\
      "}"
  status = web_view.CallFunction(session.GetCurrentFrameId(), \
               kGetWindowPositionScript, [], result);
  if status.IsError():
    return status

  value.clear()
  value.update(result)
  return Status(kOk)

def ExecuteGetCookies(session, web_view, params, value):
  cookies = []
  status = _GetVisibleCookies(web_view, cookies)
  if status.IsError():
    return status
  cookie_list = []
  for it in cookies:
    cookie_list.append(_CreateDictionaryFrom(it))

  value.clear()
  value.update({"value": cookie_list})
  return Status(kOk)

def ExecuteAddCookie(session, web_view, params, value):
  cookie = params.get("cookie")
  if type(cookie) != dict:
    return Status(kUnknownError, "missing 'cookie'")
  args = []
  args.append(cookie)
  
  status = web_view.CallFunction(session.GetCurrentFrameId(), kAddCookieScript, args, {})
  return status

def ExecuteDeleteCookie(session, web_view, params, value):
  name = params.get("name")
  if type(name) != str:
    return Status(kUnknownError, "missing 'name'")
  (status, url) = _GetUrl(web_view, session.GetCurrentFrameId())
  if status.IsError():
    return status

  return web_view.DeleteCookie(name, url)
  
def ExecuteDeleteAllCookies(session, web_view, params, value):
  cookies = []
  status = _GetVisibleCookies(web_view, cookies)
  if status.IsError():
    return status

  if cookies:
    (status, url) = _GetUrl(web_view, session.GetCurrentFrameId())
    if status.IsError():
      return status
    for it in cookies:
      status = web_view.DeleteCookie(it.name, url)
      if status.IsError():
        return status
  return Status(kOk)

def ExecuteSwitchToFrame(session, web_view, params, value):
  if not params.has_key("id"):
    return Status(kUnknownError, "missing 'id'")

  id_value = params["id"]
  if id_value == None:
    session.SwitchToTopFrame()
    return Status(kOk)

  script = ""
  args = []
  if type(id_value) == dict:
    script = "function(elem) { return elem; }"
    args.append(id_value)
  else:
    script = \
        "function(xpath) {"\
        "  return document.evaluate(xpath, document, null, "\
        "      XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;"\
        "}"
    xpath = "(/html/body//iframe|/html/frameset/frame)"
    if type(id_value) == str:
      xpath += '[@name="%s" or @id="%s"]' % (id_value, id_value)
    elif type(id_value) == int:
      xpath += "[%d]" % (id_value + 1)
    else:
      return Status(kUnknownError, "invalid 'id'")
    args.append(xpath)


  (status, frame) = web_view.GetFrameByFunction(session.GetCurrentFrameId(), script, args)
  if status.IsError():
    return status

  result = {}
  status = web_view.CallFunction(session.GetCurrentFrameId(), script, args, result)
  if status.IsError():
    return status

  if type(result) != dict:
    return Status(kUnknownError, "fail to locate the sub frame element")

  xwalk_driver_id = GenerateId()
  kSetFrameIdentifier = \
      "function(frame, id) {"\
      "  frame.setAttribute('cd_frame_id_', id);"\
      "}"
  new_args = []
  new_args.append(result)
  new_args.append(xwalk_driver_id);
  result = {}
  status = web_view.CallFunction(session.GetCurrentFrameId(), kSetFrameIdentifier, new_args, result)
  if status.IsError():
    return status
  session.SwitchToSubFrame(frame, xwalk_driver_id)
  return Status(kOk)

