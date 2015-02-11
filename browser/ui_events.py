__all__ = ["MouseEvent", \
           "TouchEvent", \
           "KeyEvent", \
           "kPressedMouseEventType", \
           "kReleasedMouseEventType", \
           "kMovedMouseEventType", \
           "kLeftMouseButton", \
           "kMiddleMouseButton", \
           "kRightMouseButton", \
           "kNoneMouseButton", \
           "kTouchStart", \
           "kTouchEnd", \
           "kTouchMove", \
           "kKeyDownEventType", \
           "kKeyUpEventType", \
           "kRawKeyDownEventType", \
           "kCharEventType", \
           "kAltKeyModifierMask", \
           "kControlKeyModifierMask", \
           "kMetaKeyModifierMask", \
           "kShiftKeyModifierMask", \
           "kNumLockKeyModifierMask"]

# Specifies the type of the mouse event.
kPressedMouseEventType = 0
kReleasedMouseEventType = 1
kMovedMouseEventType = 2

# Specifies the mouse buttons.
kLeftMouseButton = 0
kMiddleMouseButton = 1
kRightMouseButton = 2
kNoneMouseButton = 3

# Specifies the type of the touch event.
kTouchStart = 0
kTouchEnd = 1
kTouchMove = 2

# Specifies the type of the keyboard event.
kKeyDownEventType = 0
kKeyUpEventType = 1
kRawKeyDownEventType = 2
kCharEventType = 3


# Specifies modifier keys as stated in
# third_party/WebKit/Source/WebCore/inspector/Inspector.json.
# Notice: |kNumLockKeyModifierMask| is for usage in the key_converter.cc
#         and keycode_text_conversion_x.cc only, not for inspector.
kAltKeyModifierMask = 1 << 0
kControlKeyModifierMask = 1 << 1
kMetaKeyModifierMask = 1 << 2
kShiftKeyModifierMask = 1 << 3
kNumLockKeyModifierMask = 1 << 4

class MouseEvent(object):

  def __init__(self, mouse_event_type, mouse_button, x, y, modifiers, click_count):
    self.typer = mouse_event_type
    self.button = mouse_button
    self.x = x
    self.y = y
    self.modifiers = modifiers
    # |click_count| should not be negative.
    self.click_count = click_count

class TouchEvent(object):

  def __init_(self, touch_event_type, x, y):
    self.typer = touch_event_type
    self.x = x
    self.y = y

class KeyEvent(object):

  def __init__(self, key_event_type, modifiers, modified_text, unmodified_text, key_code):
    self.typer = key_event_type
    self.modifiers = modifiers
    self.modified_text = modified_text
    self.unmodified_text = unmodified_text
    self.key_code = key_code

