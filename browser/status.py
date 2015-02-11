kOk = 0
kNoSuchSession = 6
kNoSuchElement = 7
kNoSuchFrame = 8
kUnknownCommand = 9
kStaleElementReference = 10
kElementNotVisible = 11
kInvalidElementState = 12
kUnknownError = 13
kJavaScriptError = 17
kXPathLookupError = 19
kTimeout = 21
kNoSuchWindow = 23
kInvalidCookieDomain = 24
kUnexpectedAlertOpen = 26
kNoAlertOpen = 27
kScriptTimeout = 28
kInvalidSelector = 32
kSessionNotCreatedException = 33
# Xwalk-specific status codes.
kXwalkNotReachable = 100
kNoSuchExecutionContext = 101
kDisconnected = 102
kForbidden = 103
kTabCrashed = 104

class _DefaultMessageForStatusCode(object):

  """ Returns the string equivalent of the given |ErrorCode|."""
  Message = {
    kOk: "ok",
    kNoSuchSession: "no such session",
    kNoSuchElement: "no such element",
    kNoSuchFrame: "no such frame",
    kUnknownCommand: "unknown command",
    kStaleElementReference: "stale element reference",
    kElementNotVisible: "element not visible",
    kInvalidElementState: "invalid element state",
    kUnknownError: "unknown error",
    kJavaScriptError: "javascript error",
    kXPathLookupError: "xpath lookup error",
    kTimeout: "timeout",
    kNoSuchWindow: "no such window",
    kInvalidCookieDomain: "invalid cookie domain",
    kUnexpectedAlertOpen: "unexpected alert open",
    kNoAlertOpen: "no alert open",
    kScriptTimeout: "asynchronous script timeout",
    kInvalidSelector: "invalid selector",
    kSessionNotCreatedException: "session not created exception",
    kNoSuchExecutionContext: "no such execution context",
    kXwalkNotReachable: "xwalk not reachable",
    kDisconnected: "disconnected",
    kForbidden: "forbidden",
    kTabCrashed: "tab crashed",
  }

class Status(object):

  def __init__(self, code=kOk, details=""):
    self.code = code
    if type(details) == str and details:
      self.msg = _DefaultMessageForStatusCode.Message[code] + ":" + details
    else:
      self.msg = _DefaultMessageForStatusCode.Message[code]

  def Update(self, other):
    self.code = other.code
    self.msg = other.msg

  def IsOk(self):
    return self.code == kOk

  def IsError(self):
    return self.code != kOk

  def Code(self):
    return self.code

  def Message(self):
    return self.msg

  def AddDetails(self, details):
    self.msg += details

