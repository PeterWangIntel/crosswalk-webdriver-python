__all__ = ["ParseFromValue", \
           "CreateValueFrom", \
           "CreateElement", \
           "CallAtomsJs", \
           "VerifyElementClickable", \
           "FindElement", \
           "IsElementEnabled", \
           "IsOptionElementSelected", \
           "GetElementSize", \
           "IsElementDisplayed", \
           "IsOptionElementTogglable",\
           "SetOptionElementSelected", \
           "GetActiveElement", \
           "GetElementAttribute", \
           "GetElementTagName", \
           "IsElementFocused", \
           "ToggleOptionElement", \
           "GetElementRegion", \
           "GetElementEffectiveStyle", \
           "GetElementBorder", \
           "ScrollElementRegionIntoViewHelper", \
           "IsElementAttributeEqualToIgnoreCase", \
           "ScrollElementRegionIntoView", \
           "ScrollElementIntoView", \
           "GetElementClickableLocation"]

import time
import copy
from misc.basic_types import WebPoint
from misc.basic_types import WebSize
from misc.basic_types import WebRect
from third_party.atoms import *
from browser.status import *
from browser.js import *

kElementKey = "ELEMENT"

def ParseFromValue(value, target):
  if type(value) != dict:
    return False
  # target is WebPoint
  if isinstance(target, WebPoint):
    x = value.get("x")
    y = value.get("y")
    if type(x) in [float, int] and type(y) in [float, int]:
      target.x = int(x)
      target.y = int(y)
      return True
    return False
  # target is WebSize
  if isinstance(target, WebSize):
    width = value.get("width")
    height = value.get("height")
    if type(width) in [float, int] and type(height) in [float, int]:
      target.width = int(width)
      target.height = int(height)
      return True
    return False
  # target is WebRect
  if isinstance(target, WebRect):
    x = value.get("left")
    y = value.get("top")
    width = value.get("width")
    height = value.get("height")
    if type(x) in [float, int] and type(y) in [float, int] and type(width) in [float, int] and type(height) in [float, int]:
      target.origin.x = int(x)
      target.origin.y = int(y)
      target.size.width = int(width)
      target.size.height = int(height)
      return True
    return False
  
def CreateValueFrom(target):
  dict_value = {}
  # create value from WebPoint
  if isinstance(target, WebPoint):
    dict_value["x"] = target.x
    dict_value["y"] = target.y
    return dict_value
  # create value from WebSize
  if isinstance(target, WebSize):
    dict_value["width"] = target.width
    dict_value["height"] = target.height
    return dict_value
  # create value from WebRect 
  if isinstance(target, WebRect):
    dict_value["left"] = target.X()
    dict_value["right"] = target.Y()
    dict_value["width"] = target.Width()
    dict_value["height"] = target.Height()
    return dict_value

def CreateElement(element_id):
  element = {}
  element[kElementKey] = element_id
  return element

def CallAtomsJs(frame, web_view, atom_function, args, result):
  return web_view.CallFunction(frame, atom_function, args, result)

def VerifyElementClickable(frame, web_view, element_id, location):
  args = []
  args.append(CreateElement(element_id))
  args.append(CreateValueFrom(location))
  result = {}
  status = CallAtomsJs(frame, web_view, IS_ELEMENT_CLICKABLE, args, result)
  if status.IsError():
    return status
  is_clickable = False
  is_clickable = result["value"].get("clickable")
  if type(is_clickable) != bool:
    return Status(kUnknownError, "failed to parse value of IS_ELEMENT_CLICKABLE")
  if not is_clickable:
    message = result.get("message")
    if type(message) != str:
      message = "element is not clickable"
    return Status(kUnknownError, message)
  return Status(kOk)

def FindElement(interval_ms, only_one, root_element_id, session, web_view, params, value):
  strategy = params.get("using")
  if type(strategy) != str:
    return Status(kUnknownError, "'using' must be a string")
  target = params.get("value")
  if type(target) != str:
    return Status(kUnknownError, "'value' must be a string")

  script = FIND_ELEMENT if only_one else FIND_ELEMENTS
  locator = {}
  locator[strategy] = target
  arguments = []
  arguments.append(locator)
  if root_element_id:
    arguments.append(CreateElement(root_element_id))

  start_time = time.time()
  while True: 
    temp = {}
    status = web_view.CallFunction(session.GetCurrentFrameId(), script, arguments, temp)
    if status.IsError():
      return status
    # no matter what kind of result, it will packed in {"value": RemoteObject} format
    # RemoteObject can be JSON type
    if temp != {}:
      if only_one:
        value.clear()
        value.update(temp)
        return Status(kOk)
      else:
        if type(temp["value"]) != list:
          return Status(kUnknownError, "script returns unexpected result")
        if len(temp["value"]) > 0:
          value.clear()
          value.update(temp)
          return Status(kOk)

    if ((time.time() - start_time) >= session.implicit_wait):
      if only_one:
        return Status(kNoSuchElement)
      else:
        value.update({"value": []})
        return Status(kOk)

    time.sleep(float(interval_ms)/1000)
  return Status(kUnknownError)

# return status and is_enabled<bool>
def IsElementEnabled(session, web_view, element_id):
  is_enabled = False
  args = []
  args.append(CreateElement(element_id))
  result = {}
  status = CallAtomsJs(session.GetCurrentFrameId(), web_view, IS_ENABLED, args, result)
  if status.IsError():
    return (status, is_enabled)
  # we packed everything in key "value", remember?
  is_enabled = result["value"]
  if type(is_enabled) != bool:
    return (Status(kUnknownError, "IS_ENABLED should return a boolean value"), False)
  return (Status(kOk), is_enabled)

# return status and is_selected<bool>
def IsOptionElementSelected(session, web_view, element_id):
  is_selected = False
  args = []
  args.append(CreateElement(element_id))
  result = {}
  status = CallAtomsJs(session.GetCurrentFrameId(), web_view, IS_SELECTED, args, result)
  if status.IsError():
    return (status, is_selected)
  # we packed everything in key "value", remember?
  is_selected = result["value"]
  if type(is_selected) != bool:
    return (Status(kUnknownError, "IS_SELECTED should return a boolean value"), False)
  return (Status(kOk), is_selected)

def GetElementSize(session, web_view, element_id, size):
  args = []
  args.append(CreateElement(element_id))
  result = {}
  status = CallAtomsJs(session.GetCurrentFrameId(), web_view, GET_SIZE, args, result)
  if status.IsError():
    return status
  # we packed everything in key "value", remember?
  if not ParseFromValue(result["value"], size):
    return Status(kUnknownError, "failed to parse value of GET_SIZE")
  return Status(kOk)

# return status and is_displayed<bool>
def IsElementDisplayed(session, web_view, element_id, ignore_opacity):
  is_displayed = False
  args = []
  args.append(CreateElement(element_id))
  args.append(ignore_opacity)
  result = {}
  status = CallAtomsJs(session.GetCurrentFrameId(), web_view, IS_DISPLAYED, args, result)
  if status.IsError():
    return (status, is_displayed)
  # we packed everything in key "value", remember?
  is_displayed = result["value"] 
  if type(is_displayed) != bool:
    return (Status(kUnknownError, "IS_DISPLAYED should return a boolean value"), False)
  return (Status(kOk), is_displayed)

# return status and is_togglable<bool>
def IsOptionElementTogglable(session, web_view, element_id):
  is_togglable = False
  args = []
  args.append(CreateElement(element_id))
  result = {}
  status = web_view.CallFunction(session.GetCurrentFrameId(), kIsOptionElementToggleableScript, args, result)
  if status.IsError():
    return (status, is_togglable)
  # we packed everything in key "value", remember?
  is_togglable = result["value"]
  if type(is_togglable) != bool:
    return (Status(kUnknownError, "failed check if option togglable or not"), False)
  return (Status(kOk), is_togglable)

def SetOptionElementSelected(session, web_view, element_id, selected):
  # TODO(wyh): need to fix throwing error if an alert is triggered.
  args = []
  args.append(CreateElement(element_id))
  args.append(selected)
  return CallAtomsJs(session.GetCurrentFrameId(), web_view, CLICK, args, {})

def GetActiveElement(session, web_view, value):
  return web_view.CallFunction(session.GetCurrentFrameId(), "function() { return document.activeElement || document.body }", [], value)

def GetElementAttribute(session, web_view, element_id, attribute_name, value):
  args = []
  args.append(CreateElement(element_id))
  args.append(attribute_name)
  return CallAtomsJs(session.GetCurrentFrameId(), web_view, GET_ATTRIBUTE, args, value)

# return status and name<string>
def GetElementTagName(session, web_view, element_id):
  name = ""
  args = []
  args.append(CreateElement(element_id))
  result = {}
  status = web_view.CallFunction(session.GetCurrentFrameId(), "function(elem) { return elem.tagName.toLowerCase(); }", args, result)
  if status.IsError():
    return (status, name)
  # we packed everything in key "value", remember?
  name = result["value"]
  if type(name) != str:
    return (Status(kUnknownError, "failed to get element tag name"), "")
  return (Status(kOk), name)

# return status and is_focused<bool>
def IsElementFocused(session, web_view, element_id):
  is_focused = False
  result = {}
  status = GetActiveElement(session, web_view, result)
  if status.IsError():
    return (status, is_focused)
  element_dict = CreateElement(element_id)
  # we packed everything in key "value", remember?
  is_focused = (result["value"] == element_dict)
  return (Status(kOk), is_focused)

def ToggleOptionElement(session, web_view, element_id):
  is_selected = False
  (status, is_selected) = IsOptionElementSelected(session, web_view, element_id)
  if status.IsError():
    return status
  return SetOptionElementSelected(session, web_view, element_id, not is_selected)

def GetElementRegion(session, web_view, element_id, rect):
  args = []
  args.append(CreateElement(element_id))
  result = {}
  status = web_view.CallFunction(session.GetCurrentFrameId(), kGetElementRegionScript, args, result)
  if status.IsError():
    return status
  if not ParseFromValue(result["value"], rect):
    return Status(kUnknownError, "failed to parse value of getElementRegion")
  return Status(kOk)

# return status and value<string>
def GetElementEffectiveStyle(frame, web_view, element_id, sproperty):
  style = ""
  args = []
  args.append(CreateElement(element_id))
  args.append(sproperty)
  result = {}
  status = web_view.CallFunction(frame, GET_EFFECTIVE_STYLE, args, result)
  if status.IsError():
    return (status, style)
  style = result["value"]
  if type(style) != str:
    return (Status(kUnknownError, "failed to parse value of GET_EFFECTIVE_STYLE"), "")
  return (Status(kOk), style)

# return status and border_left<int> and border_top<int>
def GetElementBorder(frame, web_view, element_id):
  (status, border_left_str) = GetElementEffectiveStyle(frame, web_view, element_id, "border-left-width")
  if status.IsError():
    return (status, -1, -1)
  (status, border_top_str) = GetElementEffectiveStyle(frame, web_view, element_id, "border-top-width")
  if status.IsError():
    return (status, -1, -1)
  try:
    border_left = int(border_left_str)
    border_top = int(border_top_str)
  except:
    return (Status(kUnknownError, "failed to get border width of element"), -1, -1)
  return (Status(kOk), border_left, border_top)

def ScrollElementRegionIntoViewHelper(frame, web_view, element_id, region, center, clickable_element_id, location):
  tmp_location = copy.deepcopy(location)
  args = []
  args.append(CreateElement(element_id))
  args.append(CreateValueFrom(region))
  args.append(center)
  # TODO(wyh): why append the following param between above two cause the null value of y?
  result = {}
  status = web_view.CallFunction(frame, GET_LOCATION_IN_VIEW, args, result)
  if status.IsError():
    return status
  if not ParseFromValue(result["value"], tmp_location):
    return Status(kUnknownError, "failed to parse value of GET_LOCATION_IN_VIEW")
  if clickable_element_id:
    middle = copy.deepcopy(tmp_location)
    middle.Offset(region.Width() / 2, region.Height() / 2)
    status = VerifyElementClickable(frame, web_view, clickable_element_id, middle)
    if status.IsError():
      return status
  location.Update(tmp_location)
  return Status(kOk)

# return status and is_equal<bool>
def IsElementAttributeEqualToIgnoreCase(session, web_view, element_id, attribute_name, attribute_value):
  is_equal = False
  result = {}
  status = GetElementAttribute(session, web_view, element_id, attribute_name, result)
  if status.IsError():
    return (status, is_equal)
  actual_value = result["value"]
  if type(actual_value) == str:
    is_equal = (actual_value.lower() == attribute_value.lower())
  else:
    is_equal = False
  return (status, is_equal)

def ScrollElementRegionIntoView(session, web_view, element_id, region, center, clickable_element_id, location):
  region_offset = region.origin;
  region_size = region.size;
  status = ScrollElementRegionIntoViewHelper(session.GetCurrentFrameId(), web_view, element_id, \
                                              region, center, clickable_element_id, region_offset)
  if status.IsError():
    return status
  kFindSubFrameScript = \
      "function(xpath) {"\
      "  return document.evaluate(xpath, document, null,"\
      "      XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;"\
      "}"
  session_frames_tmp = copy.deepcopy(session.frames)
  session_frames_tmp.reverse()
  for rit in session_frames_tmp:
    args = []
    args.append("//*[@cd_frame_id_ = '%s']" % rit.xwalkdriver_frame_id)
    result = {}
    status = web_view.CallFunction(rit.parent_frame_id, kFindSubFrameScript, args, result)
    if status.IsError():
      return status
    element_dict = result["value"]
    if type(element_dict) != dict:
      return Status(kUnknownError, "no element reference returned by script")
    frame_element_id = element_dict.get(kElementKey)
    if type(frame_element_id) != str:
      return Status(kUnknownError, "failed to locate a sub frame")

    # Modify |region_offset| by the frame's border.
    (status, border_left, border_top) = GetElementBorder(rit.parent_frame_id, web_view, frame_element_id)
    if status.IsError():
      return status
    region_offset.Offset(border_left, border_top)
    status = ScrollElementRegionIntoViewHelper(rit.parent_frame_id, web_view, frame_element_id, \
                                  WebRect(region_offset, region_size), center, frame_element_id, region_offset)
    if status.IsError():
      return status
  location.Update(region_offset)
  return Status(kOk)

def ScrollElementIntoView(session, web_view, sid, location):
  size = WebSize()
  status = GetElementSize(session, web_view, sid, size);
  if status.IsError():
    return status
  status = ScrollElementRegionIntoView(session, web_view, sid, WebRect(WebPoint(0, 0), size), False, "", location)
  return status

def GetElementClickableLocation(session, web_view, element_id, location):
  (status, tag_name) = GetElementTagName(session, web_view, element_id)
  if status.IsError():
    return status
  target_element_id = element_id
  if (tag_name == "area"):
    # Scroll the image into view instead of the area.
    kGetImageElementForArea = \
        "function (element) {"\
        "  var map = element.parentElement;"\
        "  if (map.tagName.toLowerCase() != 'map')"\
        "    throw new Error('the area is not within a map');"\
        "  var mapName = map.getAttribute('name');"\
        "  if (mapName == null)"\
        "    throw new Error ('area\\'s parent map must have a name');"\
        "  mapName = '#' + mapName.toLowerCase();"\
        "  var images = document.getElementsByTagName('img');"\
        "  for (var i = 0; i < images.length; i++) {"\
        "    if (images[i].useMap.toLowerCase() == mapName)"\
        "      return images[i];"\
        "  }"\
        "  throw new Error('no img is found for the area');"\
        "}"
    args = []
    args.append(CreateElement(element_id))
    result = {}
    status = web_view.CallFunction(session.GetCurrentFrameId(), kGetImageElementForArea, args, result)
    if status.IsError():
      return status
    element_dict = result["value"]
    if type(element_dict) != dict:
      return Status(kUnknownError, "no element reference returned by script")
    target_element_id = element_dict.get(kElementKey)
    if type(target_element_id) != str: 
      return Status(kUnknownError, "no element reference returned by script")

  (status, is_displayed) = IsElementDisplayed(session, web_view, target_element_id, True)
  if status.IsError():
    return status
  if not is_displayed:
    return Status(kElementNotVisible)

  rect = WebRect()
  status = GetElementRegion(session, web_view, element_id, rect)
  if status.IsError():
    return status
  # TODO(wyh): manually change center to false make element.click() ok
  status = ScrollElementRegionIntoView(session, web_view, target_element_id, rect, False, element_id, location)
  if status.IsError():
    return status
  location.Offset(rect.Width() / 2, rect.Height() / 2)
  return Status(kOk)

