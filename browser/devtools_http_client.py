__all__ = ["DevToolsHttpClient", \
           "WebViewsInfo", \
           "WebViewInfo"]

import urllib2
import time
import yaml
from version import GetMinimumSupportedXwalkVersion
from devtools_client_impl import  DevToolsClientImpl
from web_view_impl import WebViewImpl
from status import *
from base.log import VLOG
from base.bind import Bind

def _FakeCloseFrontends():
  return Status(kOk)

def _ParseWebViewsInfo(data, views_info):
  if type(data) != list:
    return Status(kUnknownError, "DevTools did not return list")
  temp_views_info = []
  for item in data:
    if type(item) != dict:
      return Status(kUnknownError, "DevTools contains non-dictionary item")
    sid = item.get("id")
    if type(sid) != str:
      return Status(kUnknownError, "DevTools did not include id")
    type_as_string = item.get("type")
    if type(type_as_string) != str:
      return Status(kUnknownError, "DevTools did not include type")
    url = item.get("url")
    if type(url) != str:
      return Status(kUnknownError, "DevTools did not include url")
    debugger_url = item.get("webSocketDebuggerUrl")
    if type(debugger_url) != str:
      return Status(kUnknownError, "DevTools did not include debug url")
    typer = WebViewInfo.kApp
    if type_as_string == "app":
      typer = WebViewInfo.kApp
    elif type_as_string == "background_page":
      typer = WebViewInfo.kBackgroundPage
    elif type_as_string == "page":
      typer = WebViewInfo.kPage
    elif type_as_string == "worker":
      typer = WebViewInfo.kWorker
    elif type_as_string == "other":
      typer = WebViewInfo.kOther
    else:
      return Status(kUnknownError, "DevTools returned unknown type:" + type_as_string)
    temp_views_info.append(WebViewInfo(sid, debugger_url, url, typer))
  views_info.views_info = temp_views_info
  return Status(kOk)

# return status and xwalk-version
def _ParseVersionInfo(data):
  if type(data) != dict:
    return Status(kUnknownError, "version info not a dictionary"), ""
  version = data.get("Browser")
  if type(version) != str:
    return Status(kUnknownError, "Xwalk version must be >= " + \
                  GetMinimumSupportedXwalkVersion() + \
                  "version info doesn't include string 'Browser'"), ""
  return Status(kOk), version

class WebViewInfo(object):

  kApp = 0
  kBackgroundPage = 1
  kPage = 3
  kWorker = 4
  kOther = 5

  def __init__(self, sid, debugger_url, url, typer):
    self.sid = sid
    self.debugger_url = debugger_url
    self.url = url
    self.typer = typer

  def Update(self, other):
    self.sid = other.sid
    self.debugger_url = other.debugger_url
    self.url = other.url
    self.typer = other.typer

  def IsFrontend(self):
    return self.url.find("chrome-devtools://") == 0

class WebViewsInfo(object):

  def __init__(self, info=[]):
    self.views_info = info

  def Update(self, other):
    self.views_info = other.views_info

  def Get(self, index):
    return self.views_info[index]

  def GetSize(self):
    return len(self.views_info)

  def GetForId(self, sid):
    for info in self.views_info:
      if info.sid == sid:
        return info
    return None

class DevToolsHttpClient(object):

  def __init__(self, address, socket_factory):
    self.socket_factory = socket_factory
    self.server_url = "http://" + address
    self.web_socket_url_prefix = "ws://" + address + "/devtools/page/"
    self.version = ""
    self.build_no = ""

  def Update(self, other):
    self.socket_factory = other.socket_factory
    self.server_url = other.server_url
    self.web_socket_url_prefix = other.web_socket_url_prefix
    self.version = other.version
    self.build_no = other.build_no

  def Init(self, timeout):
    deadline = time.time() + timeout
    #VLOG(0, "DevTools server address is " + self.server_url)
    while True:
      status, devtools_version = self.GetVersion()
      if status.IsOk():
        break
      if status.Code() != kXwalkNotReachable or time.time() > deadline:
        return status
      time.sleep(0.05)
    kToTBuildNo = '9999'
    if not len(devtools_version):
      # Content Shell has an empty product version and a fake user agent.
      # There's no way to detect the actual version, so assume it is tip of tree.
      self.version = "content shell"
      self.build_no = kToTBuildNo
      return Status(kOk)

    if devtools_version.find("Version/") == 0:
      self.version = "webview"
      self.build_no = kToTBuildNo
      return Status(kOk)

    prefix = "Chrome/"
    if devtools_version.find(prefix) != 0:
      return Status(kUnknownError, "unrecognized Xwalk version: " + devtools_version)

    stripped_version = devtools_version[len(prefix):]
    version_parts = stripped_version.split('.')
    if len(version_parts) != 4:
      return Status(kUnknownError, "unrecognized Xwalk version: " + devtools_version)
    self.version = stripped_version
    try:
      self.build_no = str(version_parts[2])
      #VLOG(0, "we get build no: " + self.build_no)
    except:
      return Status(kUnknownError, "unrecognized Xwalk version: " + devtools_version)
    return Status(kOk)

  def GetWebViewsInfo(self, views_info):
    re, data = self.FetchUrlAndLog(self.server_url + "/json")
    if not re:
      return Status(kXwalkNotReachable)
    return _ParseWebViewsInfo(data, views_info)

  def CreateClient(self, sid):
    return DevToolsClientImpl(self.socket_factory, \
                              self.web_socket_url_prefix + sid, \
                              sid, \
                              Bind(self.CloseFrontends, [sid]))

  def CloseWebView(self, sid):
    re, data = self.FetchUrlAndLog(self.server_url + "/json/close/" + sid)
    if not re:
      return Status(kOk)
      # Closing the last web view leads xwalk to quit.
    # Wait for the target window to be completely closed.
    deadline = time.time() + 20
    while time.time() < deadline:
      views_info = WebViewsInfo()
      status = self.GetWebViewsInfo(views_info)
      if status.Code() == kXwalkNotReachable:
        return Status(kOk)
      if status.IsError():
        return status
      if not views_info.GetForId(sid):
        return Status(kOk)
      time.sleep(0.050)
    return Status(kUnknownError, "failed to close window in 20 seconds")

  def ActivateWebView(self, sid):
    re, data = self.FetchUrlAndLog(self.server_url + "/json/activate/" + sid)
    if not re:
      return Status(kUnknownError, "cannot activate web view")
    return Status(kOk)

  # return status and verison
  def GetVersion(self):
    re, data = self.FetchUrlAndLog(self.server_url + "/json/version")
    if not re:
      return Status(kXwalkNotReachable), ""
    return _ParseVersionInfo(data)
    
  def CloseFrontends(self, for_client_id):
    views_info = WebViewsInfo()
    status = self.GetWebViewsInfo(views_info)
    if status.IsError():
      return status
    # Close frontends. Usually frontends are docked in the same page, although
    # some may be in tabs (undocked, xwalk://inspect, the DevTools
    # discovery page, etc.). Tabs can be closed via the DevTools HTTP close
    # URL, but docked frontends can only be closed, by design, by connecting
    # to them and clicking the close button. Close the tab frontends first
    # in case one of them is debugging a docked frontend, which would prevent
    # the code from being able to connect to the docked one.
    tab_frontend_ids = []
    docked_frontend_ids = []
    for view_info in views_info.views_info:
      if view_info.IsFrontend():
        if view_info.typer == WebViewInfo.kPage:
          tab_frontend_ids.append(view_info.sid)
        elif view_info.typer == WebViewInfo.kOther:
          docked_frontend_ids.append(view_info.sid)
        else:
          return Status(kUnknownError, "unknown type of DevTools frontend")

    for i in tab_frontend_ids:
      status = self.CloseWebView(i)
      if status.IsError():
        return status

    for i in docked_frontend_ids:
      client = DevToolsClientImpl(self.socket_factory, \
                                  self.web_socket_url_prefix + i, \
                                  i, \
                                  Bind(FakeCloseFrontends))
      web_view = WebViewImpl(i, self.build_no, client)

      status = web_view.ConnectIfNecessary()
      # Ignore disconnected error, because the debugger might have closed when
      # its container page was closed above.
      if status.IsError() and status.Code() != kDisconnected:
        return status
      
      status, result = web_view.EvaluateScript("", "document.querySelector('*[id^=\"close-button-\"]').click();")
      # Ignore disconnected error, because it may be closed already.
      if status.IsError() and status.Code() != kDisconnected:
        return status

    # Wait until DevTools UI disconnects from the given web view. 
    deadline = time.time() + 20
    while time.time() < deadline:
      status = self.GetWebViewsInfo(view_info)
      if status.IsError():
        return status
      view_info = views_info.GetForId(for_client_id)
      if not view_info:
        return Status(kNoSuchWindow, "window was already closed")
      if len(view_info.debugger_url):
        return Status(kOk)
      time.sleep(0.050)
    return Status(kUnknownError, "failed to close UI debuggers")

  # return bool and response<list>
  def FetchUrlAndLog(self, url):
    #VLOG(1, "devtools request: " + url)
    try:
      response = urllib2.urlopen(url)
      response = yaml.load(response)
    except:
      #VLOG(1, "devtools request failed")
      return False, []
    #VLOG(1, "devtools response: " + str(response))
    return True, response

