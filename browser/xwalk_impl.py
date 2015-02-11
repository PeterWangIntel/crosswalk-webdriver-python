__all__ = ["XwalkImpl"]

from xwalk import Xwalk
from status import *
from devtools_http_client import WebViewsInfo
from devtools_http_client import WebViewInfo
from web_view_impl import WebViewImpl
from base.log import VLOG

class XwalkImpl(Xwalk):

  def __init__(self, client, devtools_event_listeners, port_reservation):
    Xwalk.__init__(self)
    self.quit = False
    self.devtools_http_client = client
    self.web_views = []
    self.devtools_event_listeners = devtools_event_listeners
    self.port_reservation = port_reservation

  def Update(self, other):
    self.quit = other.quit
    self.devtools_http_client = other.devtools_http_client
    self.web_views = other.web_views
    self.devtools_event_listeners = other.devtools_event_listeners
    self.port_reservation = other.port_reservation

  def __del__(self):
    if not self.quit:
      self.port_reservation.Leak()

  # Overridden from Xwalk:
  def GetVersion(self):
    return self.devtools_http_client.version

  def GetAsDesktop(self):
    return None

  def GetBuildNo(self):
    return self.devtools_http_client.build_no

  def HasCrashedWebView(self):
    for item in self.web_views:
      if item.WasCrashed():
        return True
    return False

  def GetWebViewIds(self, web_view_ids=[]):
    views_info = WebViewsInfo() 
    status = self.devtools_http_client.GetWebViewsInfo(views_info)
    if status.IsError():
      return status
    # Check if some web views are closed
    it = 0
    while it != len(self.web_views):
      if views_info.GetForId((self.web_views)[it].GetId()) == None:
        del (self.web_views)[it]
      else:
        it = it + 1
    # Check for newly-opened web views
    for view in views_info.views_info:
      if view.typer !=  WebViewInfo.kPage:
        continue 
      found = False
      for web_view_iter in self.web_views:
        if web_view_iter.GetId() == view.sid:
          found = True
          break
      if not found:
        client = self.devtools_http_client.CreateClient(view.sid)
        for listener in self.devtools_event_listeners:
          client.AddListener(listener)
        self.web_views.append(WebViewImpl(view.sid, self.GetBuildNo(), client))
      web_view_ids_tmp = []
      for web_view_iter in self.web_views:
        web_view_ids_tmp.append(web_view_iter.GetId())
      web_view_ids[:] = web_view_ids_tmp
      return Status(kOk)

  def GetWebViewById(self, sid, web_view):
    for item in self.web_views:
      if item.GetId() == sid:
        web_view.Update(item)
        return Status(kOk)
    return Status(kUnknownError, "webview not found")

  def CloseWebView(self, sid):
    status = self.devtools_http_client.CloseWebView(sid)
    if status.IsError():
      return status
    for item in self.web_views:
      if item.GetId() == sid:
        self.web_views.remove(item)
        break
    return Status(kOk)

  def ActivateWebView(self, sid):
    return self.devtools_http_client.ActivateWebView(sid)

  def Quit(self):
    status = self.QuitImpl()
    if status.IsOk():
      self.quit = True
    return Status(kOk)

  def QuitImpl(self):
    return Status(kOk)

