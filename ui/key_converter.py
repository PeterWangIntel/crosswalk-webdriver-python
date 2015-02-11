
from browser.status import *
from browser.ui_events import *
from keyboard_codes_posix import *

class ModifierMaskAndKeyCode(object):

  def __init__(self, mask, key_code):
    self.mask = mask
    self.key_code = key_code

  def Update(self, other):
    self.mask = other.mask
    self.key_code = other.key_code
    return

kModifiers = [ModifierMaskAndKeyCode(kShiftKeyModifierMask, VKEY_SHIFT),
              ModifierMaskAndKeyCode(kControlKeyModifierMask, VKEY_CONTROL),
              ModifierMaskAndKeyCode(kAltKeyModifierMask, VKEY_MENU)]

# TODO(wyh): Use this in KeyMap.
# Ordered list of all the key codes corresponding to special WebDriver keys.
# These WebDriver keys are defined in the Unicode Private Use Area.
# http://code.google.com/p/selenium/wiki/JsonWireProtocol#/session/:sessionId/element/:id/value
kSpecialWebDriverKeys = [
    VKEY_UNKNOWN,
    VKEY_UNKNOWN,
    VKEY_HELP,
    VKEY_BACK,
    VKEY_TAB,
    VKEY_CLEAR,
    VKEY_RETURN,
    VKEY_RETURN,
    VKEY_SHIFT,
    VKEY_CONTROL,
    VKEY_MENU,
    VKEY_PAUSE,
    VKEY_ESCAPE,
    VKEY_SPACE,
    VKEY_PRIOR,    # page up
    VKEY_NEXT,     # page down
    VKEY_END,
    VKEY_HOME,
    VKEY_LEFT,
    VKEY_UP,
    VKEY_RIGHT,
    VKEY_DOWN,
    VKEY_INSERT,
    VKEY_DELETE,
    VKEY_OEM_1,     # semicolon
    VKEY_OEM_PLUS,  # equals
    VKEY_NUMPAD0,
    VKEY_NUMPAD1,
    VKEY_NUMPAD2,
    VKEY_NUMPAD3,
    VKEY_NUMPAD4,
    VKEY_NUMPAD5,
    VKEY_NUMPAD6,
    VKEY_NUMPAD7,
    VKEY_NUMPAD8,
    VKEY_NUMPAD9,
    VKEY_MULTIPLY,
    VKEY_ADD,
    VKEY_OEM_COMMA,
    VKEY_SUBTRACT,
    VKEY_DECIMAL,
    VKEY_DIVIDE,
    VKEY_UNKNOWN,
    VKEY_UNKNOWN,
    VKEY_UNKNOWN,
    VKEY_UNKNOWN,
    VKEY_UNKNOWN,
    VKEY_UNKNOWN,
    VKEY_UNKNOWN,
    VKEY_F1,
    VKEY_F2,
    VKEY_F3,
    VKEY_F4,
    VKEY_F5,
    VKEY_F6,
    VKEY_F7,
    VKEY_F8,
    VKEY_F9,
    VKEY_F10,
    VKEY_F11,
    VKEY_F12]

kWebDriverNullKey = 0xE000
kWebDriverShiftKey = 0xE008
kWebDriverControlKey = 0xE009
kWebDriverAltKey = 0xE00A
kWebDriverCommandKey = 0xE03D

# Returns whether the given key code has a corresponding printable char.
# Notice: The given key code should be a special WebDriver key code.
def IsSpecialKeyPrintable(key_code):
  return (key_code == VKEY_TAB or key_code == VKEY_SPACE or \
      key_code == VKEY_OEM_1 or key_code == VKEY_OEM_PLUS or \
      key_code == VKEY_OEM_COMMA or \
      (key_code >= VKEY_NUMPAD0 and key_code <= VKEY_DIVIDE))

# Returns whether the given key is a WebDriver key modifier.
def IsModifierKey(key):
  if (ord(key) == kWebDriverShiftKey or ord(key) == kWebDriverControlKey or \
      ord(key) == kWebDriverAltKey or ord(key) == kWebDriverCommandKey):
    return True
  else:
    return False

# Gets the key code associated with |key|, if it is a special WebDriver key.
# Returns whether |key| is a special WebDriver key. If true, |key_code| will
# be set.
# return bool and key_code<int>
def KeyCodeFromSpecialWebDriverKey(key):
  # base::char16
  index = ord(key) - 0xE000
  is_special_key = (index >= 0 and index < len(kSpecialWebDriverKeys))
  if is_special_key:
    return (is_special_key, kSpecialWebDriverKeys[index])
  return (is_special_key, VKEY_UNKNOWN)

# Gets the key code associated with |key_utf16|, if it is a special shorthand
# key. Shorthand keys are common text equivalents for keys, such as the newline
# character, which is shorthand for the return key. Returns whether |key| is
# a shorthand key. If true, |key_code| will be set and |client_should_skip|
# will be set to whether the key should be skipped.
# return bool and key_code<int> and client_should_skip<bool>
def KeyCodeFromShorthandKey(key_utf16):
  key_code = VKEY_UNKNOWN
  client_should_skip = False;
  if (key_utf16 == '\n'):
    key_code = VKEY_RETURN
  elif (key_utf16 == '\t'):
    key_code = VKEY_TAB
  elif (key_utf16 == '\b'):
    key_code = VKEY_BACK
  elif (key_utf16 == ' '):
    key_code = VKEY_SPACE
  elif (key_utf16 == '\r'):
    key_code = VKEY_UNKNOWN
    should_skip = True
  else:
    return (False, key_code, client_should_skip)

  return (True, key_code, client_should_skip)

# Convenience functions for creating |KeyEvent|s. Used by unittests.          
def CreateKeyDownEvent(key_code, modifiers):
  return KeyEvent(kRawKeyDownEventType, modifiers, "", "", key_code)

def CreateKeyUpEvent(key_code, modifiers):
  return KeyEvent(kKeyUpEventType, modifiers, "", "", key_code)

def CreateCharEvent(unmodified_text, modified_text, modifiers):
  return KeyEvent(kCharEventType, modifiers, modified_text, unmodified_text, VKEY_UNKNOWN)

# Converts keys into appropriate |KeyEvent|s. This will do a best effort      
# conversion. However, if the input is invalid it will return a status with   
# an error message. If |release_modifiers| is true, all modifiers would be    
# depressed. |modifiers| acts both an input and an output, however, only when 
# the conversion process is successful will |modifiers| be changed.           
# return status and modifiers<int>
def ConvertKeysToKeyEvents(client_keys, release_modifiers, modifiers, client_key_events):
  key_events = []
  keys = client_keys
  # Add an implicit NULL character to the end of the input to depress all
  # modifiers.
  if (release_modifiers):
    keys += unichr(kWebDriverNullKey)

  sticky_modifiers = modifiers
  for key in keys: 
    if (ord(key) == kWebDriverNullKey):
      # Release all modifier keys and clear |stick_modifiers|.
      if (sticky_modifiers & kShiftKeyModifierMask):
        key_events.append(CreateKeyUpEvent(VKEY_SHIFT, 0))
      if (sticky_modifiers & kControlKeyModifierMask):
        key_events.append(CreateKeyUpEvent(VKEY_CONTROL, 0))
      if (sticky_modifiers & kAltKeyModifierMask):
        key_events.append(CreateKeyUpEvent(VKEY_MENU, 0))
      if (sticky_modifiers & kMetaKeyModifierMask):
        key_events.append(CreateKeyUpEvent(VKEY_COMMAND, 0))
      sticky_modifiers = 0
      continue

    if (IsModifierKey(key)):
      # Press or release the modifier, and adjust |sticky_modifiers|.
      modifier_down = False
      key_code = VKEY_UNKNOWN
      if (ord(key) == kWebDriverShiftKey):
        sticky_modifiers ^= kShiftKeyModifierMask
        modifier_down = ((sticky_modifiers & kShiftKeyModifierMask) != 0)
        key_code = VKEY_SHIFT
      elif (ord(key) == kWebDriverControlKey):
        sticky_modifiers ^= kControlKeyModifierMask
        modifier_down = ((sticky_modifiers & kControlKeyModifierMask) != 0)
        key_code = VKEY_CONTROL
      elif (ord(key) == kWebDriverAltKey):
        sticky_modifiers ^= kAltKeyModifierMask
        modifier_down = ((sticky_modifiers & kAltKeyModifierMask) != 0)
        key_code = VKEY_MENU
      elif (ord(key) == kWebDriverCommandKey):
        sticky_modifiers ^= kMetaKeyModifierMask
        modifier_down = ((sticky_modifiers & kMetaKeyModifierMask) != 0)
        key_code = VKEY_COMMAND
      else:
        return (Status(kUnknownError, "unknown modifier key"), sticky_modifiers)
      if modifier_down:
        key_events.append(CreateKeyDownEvent(key_code, sticky_modifiers))
      else:
        key_events.append(CreateKeyUpEvent(key_code, sticky_modifiers))
      continue

    key_code = VKEY_UNKNOWN
    unmodified_text = ""
    modified_text = ""
    all_modifiers = sticky_modifiers

    # Get the key code, text, and modifiers for the given key.
    should_skip = False
    (is_special_key, key_code) = KeyCodeFromSpecialWebDriverKey(key)
    error_msg = ""

    (temp_flag, key_code, should_skip) = KeyCodeFromShorthandKey(key)
    if (is_special_key or temp_flag):
      if (should_skip):
        continue
      if (key_code == VKEY_UNKNOWN):
        return (Status(kUnknownError, \
            "unknown WebDriver key(%d) at string index (%s)" % (ord(key), key)), sticky_modifiers)
      if (key_code == VKEY_RETURN):
        # For some reason Xwalk expects a carriage return for the return key.
        modified_text = unmodified_text = "\r"
      elif (is_special_key and not IsSpecialKeyPrintable(key_code)):
        # To prevent char event for special keys like DELETE.
        modified_text = unmodified_text = ""
      else:
        # WebDriver assumes a numpad key should translate to the number,
        # which requires NumLock to be on with some platforms. This isn't
        # formally in the spec, but is expected by their tests.
        webdriver_modifiers = 0
        if (key_code >= VKEY_NUMPAD0 and key_code <= VKEY_NUMPAD9):
          webdriver_modifiers = kNumLockKeyModifierMask
          unmodified_text = chr(key_code - 0x30)
          modified_text = chr(key_code - 0x30)
    else:
      necessary_modifiers = 0
#      ConvertCharToKeyCode(key, &key_code, &necessary_modifiers, &error_msg);
      if error_msg:
        return (Status(kUnknownError, error_msg), sticky_modifiers)
      all_modifiers |= necessary_modifiers
      if (key_code != VKEY_UNKNOWN):
        unmodified_text = chr(key_code)
        modified_text = chr(key_code)
        if (not unmodified_text or not modified_text):
          # To prevent char event for special cases like CTRL + x (cut).
          unmodified_text = ""
          modified_text= ""
       
      else:
        # Do a best effort and use the raw key we were given.
        unmodified_text = key
        modified_text = key

    # Create the key events.
    necessary_modifiers = [0, 0, 0]
    for i in range(3):
      necessary_modifiers[i] = (all_modifiers & kModifiers[i].mask) and \
          not (sticky_modifiers & kModifiers[i].mask)
      if (necessary_modifiers[i]):
        key_events.append(CreateKeyDownEvent(kModifiers[i].key_code, sticky_modifiers))

    key_events.append(CreateKeyDownEvent(key_code, all_modifiers))
    if len(unmodified_text) or len(modified_text):
      key_events.append(CreateCharEvent(unmodified_text, modified_text, all_modifiers))

    key_events.append(CreateKeyUpEvent(key_code, all_modifiers))

    for i in range(2, -1, -1):
      if necessary_modifiers[i]:
        key_events.append(CreateKeyUpEvent(kModifiers[i].key_code, sticky_modifiers))

  client_key_events[:] = key_events
  modifiers = sticky_modifiers
  return (Status(kOk), modifiers)

