__all__ = ["ExecuteElementCommand", \
           "ExecuteFindChildElement", \
           "ExecuteFindChildElements", \
           "ExecuteGetElementText", \
           "ExecuteGetElementTagName", \
           "ExecuteIsElementSelected", \
           "ExecuteIsElementEnabled", \
           "ExecuteIsElementDisplayed", \
           "ExecuteGetElementLocation", \
           "ExecuteGetElementSize", \
           "ExecuteClearElement", \
           "ExecuteGetElementAttribute", \
           "ExecuteGetElementValue", \
           "ExecuteGetElementValueOfCSSProperty", \
           "ExecuteElementEquals", \
           "ExecuteSubmitElement", \
           "ExecuteGetElementLocationOnceScrolledIntoView", 
           "ExecuteClickElement", \
           "ExecuteSendKeysToElement"]

import time
from element_util import *
from browser.js import *
from browser.status import *
from browser.web_view_impl import WebViewImpl
from browser.ui_events import *
from third_party.atoms import *
from misc.basic_types import WebPoint
from misc.util import SendKeysOnWindow

def ExecuteElementCommand(command, element_id, session, params, value):
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
    command.Update([session, web_view, element_id, params, value])
    status = command.Run()
  nav_status = web_view.WaitForPendingNavigations(session.GetCurrentFrameId(), session.page_load_timeout, True)

  if status.IsOk() and nav_status.IsError() and nav_status.Code() != kUnexpectedAlertOpen:
    return nav_status
  if status.Code() == kUnexpectedAlertOpen:
    return Status(kOk)
  return status

def ExecuteFindChildElement(session, web_view, element_id, params, value):
  interval_ms = 50
  return FindElement(interval_ms, True, element_id, session, web_view, params, value)

def ExecuteFindChildElements(session, web_view, element_id, params, value):
  interval_ms = 50
  return FindElement(interval_ms, False, element_id, session, web_view, params, value)

def ExecuteGetElementText(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), GET_TEXT, args, value)
  
def ExecuteGetElementTagName(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), "function(elem) { return elem.tagName.toLowerCase(); }", args, value)

def ExecuteIsElementSelected(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), IS_SELECTED, args, value)

def ExecuteIsElementEnabled(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), IS_ENABLED, args, value)

def ExecuteIsElementDisplayed(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), IS_DISPLAYED, args, value)

def ExecuteGetElementLocation(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), GET_LOCATION, args, value)

def ExecuteGetElementSize(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), GET_SIZE, args, value)

def ExecuteClearElement(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  result = {}
  return web_view.CallFunction(session.GetCurrentFrameId(), CLEAR, args, result)

def ExecuteGetElementAttribute(session, web_view, element_id, params, value):
  # the desired parameter comes from url request not url content
  # we define it on our own, make the name of key look fool that will not 
  # conflict with the standard label
  name = params.get("extra_url_params")
  if type(name) != str:
    return Status(kUnknownError, "missing 'name'")
  return GetElementAttribute(session, web_view, element_id, name, value)

def ExecuteGetElementValue(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), \
        "function(elem) { return elem['value'] }", args, value)

def ExecuteGetElementValueOfCSSProperty(session, web_view, element_id, params, value):
  # the desired parameter comes from url request not url content
  # we define it on our own, make the name of key look fool that will not 
  # conflict with the standard label
  property_name = params.get("extra_url_params")
  if type(property_name) != str:
    return Status(kUnknownError, "missing 'propertyName'")
  (status, property_value) = GetElementEffectiveStyle(session.GetCurrentFrameId(), web_view, element_id, property_name)
  if status.IsError():
    return status
  value.clear()
  value.update({"value": property_value})
  return Status(kOk)

def ExecuteElementEquals(session, web_view, element_id, params, value):
  # the desired parameter comes from url request not url content
  # we define it on our own, make the name of key look fool that will not 
  # conflict with the standard label
  other_element_id = params.get("extra_url_params")
  if type(other_element_id) != str:
    return Status(kUnknownError, "'other' must be a string")
  value.clear()
  value.update({"value": (element_id == other_element_id)})
  return Status(kOk)

def ExecuteSubmitElement(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), SUBMIT, args, value)

def ExecuteGetElementLocationOnceScrolledIntoView(session, web_view, element_id, params, value):
  location = WebPoint()
  status = ScrollElementIntoView(session, web_view, element_id, location)
  if status.IsError():
    return status
  value.clear()
  value.update({"value": CreateValueFrom(location)})
  return Status(kOk)

def ExecuteTouchSingleTapAtom(session, web_view, element_id, params, value):
  args = []
  args.append(CreateElement(element_id))
  return web_view.CallFunction(session.GetCurrentFrameId(), TOUCH_SINGLE_TAP, args, value)

def ExecuteClickElement(session, web_view, element_id, params, value):
  (status, tag_name) = GetElementTagName(session, web_view, element_id)
  if status.IsError():
    return status
  if tag_name == "option":
    (status, is_toggleable) = IsOptionElementTogglable(session, web_view, element_id)
    if status.IsError():
      return status
    if is_toggleable:
      return ToggleOptionElement(session, web_view, element_id);
    else:
      return SetOptionElementSelected(session, web_view, element_id, True)
  else:
    location = WebPoint()
    status = GetElementClickableLocation(session, web_view, element_id, location)
    if status.IsError():
      return status
    
    events = []
    events.append(MouseEvent(kMovedMouseEventType, kNoneMouseButton, \
                   location.x, location.y, session.sticky_modifiers, 0))
    events.append(MouseEvent(kPressedMouseEventType, kLeftMouseButton, \
                   location.x, location.y, session.sticky_modifiers, 1))
    events.append(MouseEvent(kReleasedMouseEventType, kLeftMouseButton, \
                   location.x, location.y, session.sticky_modifiers, 1))

    status = web_view.DispatchMouseEvents(events, session.GetCurrentFrameId())
    if status.IsOk():
      session.mouse_position.Update(location)
    return status

####### remain test api #####################
def SendKeysToElement(session, web_view, element_id, key_list):
  is_displayed = False
  is_focused = False
  start_time = time.time()
  while True:
    (status, is_displayed) = IsElementDisplayed(session, web_view, element_id, True)
    if status.IsError():
      return status
    if is_displayed:
      break
    (status, is_focused) = IsElementFocused(session, web_view, element_id)
    if status.IsError():
      return status
    if is_focused:
      break
    if ((time.time() - start_time) >= session.implicit_wait):
      return Status(kElementNotVisible);
    time.sleep(0.1)

  is_enabled = False
  (status, is_enabled) = IsElementEnabled(session, web_view, element_id)
  if status.IsError():
    return status
  if not is_enabled:
    return Status(kInvalidElementState)

  if not is_focused:
    args = []
    args.append(CreateElement(element_id))
    result = {}
    status = web_view.CallFunction(session.GetCurrentFrameId(), kFocusScript, args, result)
    if status.IsError():
      return status

  (status, session.sticky_modifiers) = SendKeysOnWindow(web_view, key_list, True, session.sticky_modifiers)
  return status

def ExecuteHoverOverElement(session, web_view, element_id, params, value):
  location = WebPoint()
  status = GetElementClickableLocation(session, web_view, element_id, location)
  if status.IsError():
    return status

  move_event = MouseEvent(kMovedMouseEventType, kNoneMouseButton, location.x, location.y, session.sticky_modifiers, 0)
  events = []
  events.append(move_event)
  status = web_view.DispatchMouseEvents(events, session.GetCurrentFrameId())
  if status.IsOk():
    session.mouse_position.Update(location)
  return status

def ExecuteTouchSingleTap(session, web_view, element_id, params, value):
  # Fall back to javascript atom for pre-m30 Xwalk.
  if session.xwalk.GetBuildNo() < 1576:
    return ExecuteTouchSingleTapAtom(session, web_view, element_id, params, value)

  location = WebPoint()
  status = GetElementClickableLocation(session, web_view, element_id, location)

  if status.IsError():
    return status
  
  events = []
  events.append(TouchEvent(kTouchStart, location.x, location.y))
  events.append(TouchEvent(kTouchEnd, location.x, location.y))

  return web_view.DispatchTouchEvents(events)

def ExecuteSendKeysToElement(session, web_view, element_id, params, value):
  key_list = params.get("value")
  if type(key_list) != list:
    return Status(kUnknownError, "'value' must be a list")

  (status, is_input) = IsElementAttributeEqualToIgnoreCase(\
      session, web_view, element_id, "tagName", "input")
  if status.IsError():
    return status
  (status, is_file) = IsElementAttributeEqualToIgnoreCase(\
      session, web_view, element_id, "type", "file")
  if status.IsError():
    return status
  if is_input and is_file:
    # Compress array into a single string.
    paths_string = ""
    for path_part in key_list:
      if type(path_part) != str:
        return Status(kUnknownError, "'value' is invalid")
      paths_string += path_part

    # Separate the string into separate paths, delimited by '\n'.
    paths = paths_string.split("\n")

    (status, multiple) = IsElementAttributeEqualToIgnoreCase(\
        session, web_view, element_id, "multiple", "true")
    if status.IsError():
      return status
    if not multiple and len(paths):
      return Status(kUnknownError, "the element can not hold multiple files")

    element = CreateElement(element_id)
    return web_view.SetFileInputFiles(session.GetCurrentFrameId(), element, paths)
  else:
    return SendKeysToElement(session, web_view, element_id, key_list)

