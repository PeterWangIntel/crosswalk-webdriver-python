__all__ = ["WebViewImpl"]

from base.log import VLOG
from base.bind import Bind
from web_view import WebView
from status import *
from ui_events import * 
from js import *
from geolocation_override_manager import GeolocationOverrideManager
from debugger_tracker import DebuggerTracker
from javascript_dialog_manager import JavaScriptDialogManager
from navigation_tracker import NavigationTracker
from frame_tracker import FrameTracker
from devtools_client_impl import DevToolsClientImpl
from heap_snapshot_taker import HeapSnapshotTaker
from dom_tracker import DomTracker
import json
import copy

# EvaluateScriptReturnType 
ReturnByValue = 0
ReturnByObject = 1

# return status and context_id<int>
def _GetContextIdForFrame(tracker, frame):
  if not frame:
    return Status(kOk), 0
  (status, context_id) = tracker.GetContextIdForFrame(frame)
  if status.IsError():
    return status, 0
  return Status(kOk), context_id

def _GetMouseEventAsString(typer):
  if typer == kPressedMouseEventType:
    return "mousePressed"
  elif typer == kReleasedMouseEventType:
    return "mouseReleased"
  elif typer == kMovedMouseEventType:
    return "mouseMoved"
  else:
    return ""

def _GetTouchEventAsString(typer):
  if typer == kTouchStart:
    return "touchStart"
  elif typer == kTouchEnd:
    return "touchEnd"
  elif typer == kTouchMove:
    return "touchMove"
  else:
    return ""

def _GetMouseButtonAsString(typer):
  if typer == kLeftMouseButton:
    return "left"
  elif typer == kMiddleMouseButton:
    return "middle"
  elif typer == kRightMouseButton:
    return "right"
  elif typer == kNoneMouseButton:
    return "none"
  else:
    return ""

def _GetKeyEventAsString(typer):
  if typer == kKeyDownEventType:
    return "keyDown"
  elif typer == kKeyUpEventType:
    return "keyUp"
  elif typer == kRawKeyDownEventType:
    return "rawKeyDown"
  elif typer == kCharEventType:
    return "char"
  else:
    return ""

def _GetPointStateString(typer):
  if typer == kTouchStart:
    return "touchPressed"
  elif typer == kTouchEnd:
    return "touchReleased"
  elif typer == kTouchMove:
    return "touchMoved"
  else:
    return ""

# result = response.result.result
def _EvaluateScript(client, context_id, expression, return_type, result):
  params = {}
  params["expression"] = expression
  if context_id:
    params["contextId"] = context_id
  params["returnByValue"] = (return_type == ReturnByValue)
  cmd_result = {}
  status = client.SendCommandAndGetResult("Runtime.evaluate", params, cmd_result)
  if status.IsError():
    return status
  was_thrown = cmd_result.get("wasThrown", None)
  if type(was_thrown) != bool:
    return Status(kUnknownError, "Runtime.evaluate missing 'wasThrown'")
  if was_thrown:
    description = cmd_result.get("result.description", "unknown")
    return Status(kUnknownError, "Runtime.evaluate threw exception: " + description)
  unscoped_result = {}
  unscoped_result = cmd_result.get("result")
  if type(unscoped_result) != dict:
    return Status(kUnknownError, "evaluate missing dictionary 'result'")
  result.clear()
  result.update(unscoped_result)
  return Status(kOk)

# resturn status, got_object<bool> and object_id<string> 
def _EvaluateScriptAndGetObject(client, context_id, expression):
  result = {}
  object_id = ""
  status = _EvaluateScript(client, context_id, expression, ReturnByObject, result)
  if status.IsError():
    return (status, False, object_id)
  if not result.has_key("objectId"):
    return (Status(kOk), False, object_id)
  object_id = result.get("objectId")
  if type(object_id) != str:
    return (Status(kUnknownError, "evaluate has invalid 'objectId'"), False, object_id)
  return (Status(kOk), True, object_id)

# result = response.result.result.value
def _EvaluateScriptAndGetValue(client, context_id, expression, result):
  temp_result = {}
  status = _EvaluateScript(client, context_id, expression, ReturnByValue, temp_result)
  if status.IsError():
    return status
  typer = temp_result.get("type")
  if type(typer) != str:
    return Status(kUnknownError, "Runtime.evaluate missing string 'type'")
  if typer == "undefined":
    result.clear()
  else:
    if not temp_result.has_key("value"):
      return Status(kUnknownError, "Runtime.evaluate missing 'value'")
    result.clear()
    # packed in a dict to make pass like point
    if type(temp_result["value"]) != dict:
      result.update({"value": temp_result["value"]})
    else:
      result.update(temp_result["value"])
  return Status(kOk)

# return status, found_node<bool> and node_id<int>
def _GetNodeIdFromFunction(client, context_id, function, args):
  node_id = -1
  try:
    js = json.dumps(args)
  except:
    return (Status(kUnknownError, "json dumps error"), False, node_id)
  # TODO(wyh): Second null should be array of shadow host ids.
  expression = "(%s).apply(null, [null, %s, %s, true])" % (kCallFunctionScript, function, js)
  (status, got_object, element_id) = _EvaluateScriptAndGetObject(client, context_id, expression)
  if status.IsError():
    return (status, False, node_id)
  if not got_object:
    return (Status(kOk), False, node_id)
  cmd_result = {}
  params = {}
  params["objectId"] = element_id
  status = client.SendCommandAndGetResult("DOM.requestNode", params, cmd_result)
  # Release the remote object before doing anything else.
  params = {}
  params["objectId"] = element_id
  release_status = client.SendCommand("Runtime.releaseObject", params)
  if release_status.IsError():
    VLOG(3, "Failed to release remote object: " + release_status.Message())
  if status.IsError():
    return (status, False, node_id)
  node_id = cmd_result.get("nodeId")
  if type(node_id) != int:
    return (Status(kUnknownError, "DOM.requestNode missing int 'nodeId'"), False, node_id)
  return (Status(kOk), True, node_id)

def _ParseCallFunctionResult(dic, result):
  if type(dic) != dict: 
    return Status(kUnknownError, "call function result must be a dictionary")
  status_code = dic.get("status", None)
  if type(status_code) != int:
    return Status(kUnknownError, "call function result missing int 'status'")
  if status_code != kOk:
    message = dic.get("value", "")
    return Status(status_code, message)
  if not dic.has_key("value"):
    return Status(kUnknownError, "call function result missing 'value'")
  result.clear()
  result.update({"value": dic["value"]})
  return Status(kOk)

class WebViewImpl(WebView):

  def __init__(self, sid, build_no, client):
    WebView.__init__(self, sid)
    self.build_no = build_no
    self.client = client
    # in case of casually init DevToolsClientImpl, may cause wrong init of DevToolsEventListener
    if isinstance(client, DevToolsClientImpl):
      self.dom_tracker = DomTracker(client)
      self.frame_tracker = FrameTracker(client)
      self.navigation_tracker = NavigationTracker(client)
      self.dialog_manager = JavaScriptDialogManager(client)
      self.geolocation_override_manager = GeolocationOverrideManager(client)
      self.heap_snapshot_taker = HeapSnapshotTaker(client)
      #self.debugger = DebuggerTracker(client)
    else:
      self.dom_tracker = None
      self.frame_tracker = None
      self.navigation_tracker = None
      self.dialog_manager = None
      self.geolocation_override_manager = None
      self.heap_snapshot_taker = None
      #self.debugger = None

  def Update(self, other):
    self.build_no = other.build_no
    self.client = other.client
    self.dom_tracker = other.dom_tracker
    self.frame_tracker = other.frame_tracker
    self.navigation_tracker = other.navigation_tracker
    self.dialog_manager = other.dialog_manager
    self.geolocation_override_manager = other.geolocation_override_manager
    self.heap_snapshot_taker = other.heap_snapshot_taker
    #self.debugger = other.debugger

  # Overridden from WebView:
  def GetId(self):
    return self.sid

  def WasCrashed(self):
    return self.client.WasCrashed()

  def ConnectIfNecessary(self):
    return self.client.ConnectIfNecessary()

  def HandleReceivedEvents(self):
    return self.client.HandleReceivedEvents()

  def Load(self, url):
    # Javascript URLs will cause a hang while waiting for the page to stop
    # loading, so just disallow.
    if url.lower().startswith("javascript"):
      return Status(kUnknownError, "unsupported protocol")
    params = {}
    params["url"] = url
    return self.client.SendCommand("Page.navigate", params)

  def Reload(self):
    params = {}
    params["ignoreCache"] = False
    return self.client.SendCommand("Page.reload", params)

  def DispatchTouchEvents(self, events=[]):
    for it in events:
      params = {}
      params["type"] = _GetTouchEventAsString(it.typer)
      point_list = []
      point = {}
      point["state"] = _GetPointStateString(it.typer)
      point["x"] = it.x
      point["y"] = it.y
      point_list[0] = point
      params["touchPoints"] = point_list
      status = self.client.SendCommand("Input.dispatchTouchEvent", params)
      if status.IsError():
        return status
    return Status(kOk)
 
  def DispatchKeyEvents(self, events=[]):
    for it in events:
      params = {}
      params["type"] = _GetKeyEventAsString(it.typer)
      if it.modifiers & kNumLockKeyModifierMask:
        params["isKeypad"] = True
        params["modifiers"] = it.modifiers & (kNumLockKeyModifierMask - 1)
      else:
        params["modifiers"] = it.modifiers
      params["text"] = it.modified_text
      params["unmodifiedText"] = it.unmodified_text
      params["nativeVirtualKeyCode"] = it.key_code
      params["windowsVirtualKeyCode"] = it.key_code
      status = self.client.SendCommand("Input.dispatchKeyEvent", params)
      if status.IsError():
        return status
    return Status(kOk)
  
  def DispatchMouseEvents(self, events, frame):
    for it in events:
      params = {}
      params["type"] = _GetMouseEventAsString(it.typer)
      params["x"] = it.x
      params["y"] = it.y
      params["modifiers"] = it.modifiers
      params["button"] = _GetMouseButtonAsString(it.button)
      params["clickCount"] = it.click_count
      status = self.client.SendCommand("Input.dispatchMouseEvent", params)
      if status.IsError():
        return status
      if self.build_no < 1569 and it.button == kRightMouseButton and it.typer == kReleasedMouseEventType:
        args = []
        args.append(it.x)
        args.append(it.y)
        args.append(it.modifiers)
        result = {}
        status = self.CallFunction(frame, kDispatchContextMenuEventScript, args, result)
        if status.IsError():
          return status
    return Status(kOk)

  def GetCookies(self, cookies=[]):
    params = {}
    result = {}
    status = self.client.SendCommandAndGetResult("Page.getCookies", params, result)
    if status.IsError():
      return status
    cookies_tmp = result.get("cookies")
    if type(cookies_tmp) != list:
      return Status(kUnknownError, "DevTools didn't return cookies")
    cookies[:] = cookies_tmp
    return Status(kOk)

  def DeleteCookie(self, name, url):
    params = {}
    params["cookieName"] = name
    params["url"] = url
    return self.client.SendCommand("Page.deleteCookie", params)

  def GetJavaScriptDialogManager(self):
    return self.dialog_manager

  def OverrideGeolocation(self, geoposition):
    return self.geolocation_override_manager.OverrideGeolocation(geoposition)

  def EvaluateScript(self, frame, expression, result):
    (status, context_id) = _GetContextIdForFrame(self.frame_tracker, frame)
    if status.IsError():
      return status
    return _EvaluateScriptAndGetValue(self.client, context_id, expression, result)

  def CallFunction(self, frame, function, args, result):
    try:
      js = json.dumps(args)
    except:
      return Status(kUnknownError)
    # TODO(wyh): Second null should be array of shadow host ids.
    expression = "(%s).apply(null, [null, %s, %s])" % (kCallFunctionScript, function, js)
    temp_result = {}
    status = self.EvaluateScript(frame, expression, temp_result)
    if status.IsError():
      return status
    return _ParseCallFunctionResult(temp_result, result)
 
  def CallAsyncFunctionInternal(self, frame, function, args, is_user_supplied, timeout, result):
    async_args = []
    async_args.append("return (" + function + ").apply(null, arguments);")
    async_args.extend(args)
    async_args.append(is_user_supplied)
    # timeout should be in milliseconds
    async_args.append(timeout)
    tmp = {}
    status = self.CallFunction(frame, kExecuteAsyncScriptScript, async_args, tmp)
    if status.IsError():
      return status
    kDocUnloadError = "document unloaded while waiting for result"
    kQueryResult = "function() {\
         var info = document.$xwalk_asyncScriptInfo;\
         if (!info)\
           return {status: %d, value: '%s'};\
         var result = info.result;\
         if (!result)\
           return {status: 0};\
         delete info.result;\
         return result;\
       }" % (kJavaScriptError, kDocUnloadError)
    while True:
      no_args = []
      query_value = {}
      status = self.CallFunction(frame, kQueryResult, no_args, query_value)
      if status.IsError():
        if status.Code() == kNoSuchFrame:
          return Status(kJavaScriptError, kDocUnloadError)
        return status
      if type(query_value) != dict:
        return Status(kUnknownError, "async result info is not a dictionary")
      status_code = query_value.get("status", None)
      if type(status_code) != int:
        return Status(kUnknownError, "async result info has no int 'status'")
      if status_code != kOk:
        return Status(status_code, str(query_value.get("value")))
      if query_value.has_key("value"):
        result.clear()
        result.update(query_value["value"])
        return Status(kOk)
      time.sleep(0.1)

  def CallAsyncFunction(self, frame, function, args, timeout, result):
    return self.CallAsyncFunctionInternal(frame, function, args, False, timeout, result)

  def CallUserAsyncFunction(self, frame, function, args, timeout, result):
    return self.CallAsyncFunctionInternal(frame, function, args, True, timeout, result)
 
  # return status and is_not_pending<bool>
  def IsNotPendingNavigation(self, frame_id):
    (status, is_pending) = self.navigation_tracker.IsPendingNavigation(frame_id)
    if status.IsError():
      return (status, True)
    if is_pending and self.dialog_manager.IsDialogOpen():
      return (Status(kUnexpectedAlertOpen), False)
    is_not_pending = not is_pending
    return (Status(kOk), is_not_pending)

  # return status and is_pending<bool>
  def IsPendingNavigation(self, frame_id):
    return self.navigation_tracker.IsPendingNavigation(frame_id)

  def WaitForPendingNavigations(self, frame_id, timeout, stop_load_on_timeout):
    VLOG(0, "Waiting for pending navigations...")
    status = self.client.HandleEventsUntil(Bind(self.IsNotPendingNavigation, [frame_id]), timeout)
    if status.Code() == kTimeout and stop_load_on_timeout:
      VLOG(0, "Timed out. Stopping navigation...")
      unused_value = {}
      self.EvaluateScript("", "window.stop();", unused_value)
      new_status = self.client.HandleEventsUntil(Bind(self.IsNotPendingNavigation, [frame_id]), 10)
      if new_status.IsError():
        status = new_status
    VLOG(0, "Done waiting for pending navigations")
    return status

  def TakeHeapSnapshot(self):
    return self.heap_snapshot_taker.TakeHeapSnapshot()

  # return status and out_frame<string>
  def GetFrameByFunction(self, frame, function, args):
    (status, context_id) = _GetContextIdForFrame(self.frame_tracker, frame)
    if status.IsError():
      return status
    found_node = False
    node_id = -1
    (status, found_node, node_id) = _GetNodeIdFromFunction(self.client, context_id, function, args)
    if status.IsError():
      return status
    if not found_node:
      return Status(kNoSuchFrame)
    return self.dom_tracker.GetFrameIdForNode(node_id)

  def SetFileInputFiles(self, frame, element, files):
    file_list = []
    for i in files:
      if not i.startswith("/"):
        return Status(kUnknownError, "path is not absolute: " + i)
      if i.find(".") != -1:
        return Status(kUnknownError, "path is not canonical: " + i)
      file_list.append(i)

    (status, context_id) = _GetContextIdForFrame(self.frame_tracker, frame)
    if status.IsError():
      return status
    args = []
    args.append(copy.deepcopy(element))
    (status, found_node, node_id) = _GetNodeIdFromFunction(self.client, context_id, "function(element) { return element; }", args)
    if status.IsError():
      return status
    if not found_node:
      return Status(kUnknownError, "no node ID for file input")
    params = {}
    params["nodeId"] = node_id
    params["files"] = file_list
    return self.client.SendCommand("DOM.setFileInputFiles", params)

  # return status and screenshot<string>
  def CaptureScreenshot(self):
    result = {}
    status = self.client.SendCommandAndGetResult("Page.captureScreenshot", {}, result)
    if status.IsError():
      return (status, "")
    screenshot = result.get("data")
    if type(screenshot) != str:
      return (Status(kUnknownError, "expected string 'data' in response"), "")
    return (Status(kOk), screenshot)

