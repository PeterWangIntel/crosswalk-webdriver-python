from browser.status import *
from ui.key_converter import ConvertKeysToKeyEvents

# return status and dest<string>
def FlattenStringArray(src):
  dest = ""
  for i in src:
    if type(i) != str:
      return (Status(kUnknownError, "keys should be a string"), "")
    dest = dest + i
  return (Status(kOk), dest)

# return status and sticky_modifiers<int>
def SendKeysOnWindow(web_view, key_list, release_modifiers, sticky_modifiers):
  (status, keys) = FlattenStringArray(key_list)
  if status.IsError():
    return (status, sticky_modifiers)
  events = []
  sticky_modifiers_tmp = sticky_modifiers
  (status, sticky_modifiers_tmp) = ConvertKeysToKeyEvents(keys, release_modifiers, sticky_modifiers_tmp, events)
  if status.IsError():
    return (status, sticky_modifiers)
  status = web_view.DispatchKeyEvents(events)
  if status.IsOk():
    sticky_modifiers = sticky_modifiers_tmp
  return (status, sticky_modifiers)

