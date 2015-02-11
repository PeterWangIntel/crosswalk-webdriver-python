__all__ = ["Capabilities", \
           "Switches"]

from browser.status import *
from base.bind import Bind
from base.log import VLOG

class Switches(object):

  def __init__(self):
    self.switch_map = {}

  def SetSwitch(self, name, value=""):
    self.switch_map[name] = value

  # In case of same key, |switches| will override.
  def SetFromSwitches(self, switches):
    for key, value in switches.switch_map.iteritems():
      self.switch_map[key] = value

  # Sets a switch from the capabilities, of the form [--]name[=value].
  def SetUnparsedSwitch(self, unparsed_switch):
    equals_index = unparsed_switch.find('=')
    if equals_index != -1:
      value = unparsed_switch[equals_index + 1:]
    start_index = 0
    if unparsed_switch[:2] == "--":
      start_index = 2
    name = unparsed_switch[start_index:equals_index]
    self.SetSwitch(name, value)

  def RemoveSwitch(self, name):
    del self.switch_map[name]

  def HasSwitch(self, name):
    return self.switch_map.has_key[name]

  def GetSwitchValue(self, name):
    if name not in self.switch_map:
      return ""
    return self.switch_map[name]

  def GetSwitchValueNative(self, name):
    if name not in self.switch_map:
      return ""
    return self.switch_map[name]

  def GetSize(self):
    return len(self.switch_map)

  def ToString(self):
    string = ""
    for key, value in self.switch_map.iteritems():
      string += "--" + key
      if len(value):
        if value.find(" ") != -1:
          value = "true"
      string += "=" + value + " "
    return string      

def ParseBoolean(member, option, capabilities):
  if type(option) != bool:
    return Status(kUnknownError, "must be a boolean")
  elif not hasattr(capabilities, member):
    return Status(kUnknownError, "has no such member variety")
  else:
    setattr(capabilities, member, option)
    return Status(kOk)

def ParseString(member, option, capabilities):
  if type(option) != str and type(option) != unicode:
    return Status(kUnknownError, "must be a string")
  elif not option:
    return Status(kUnknownError, "cannot be empty")
  elif not hasattr(capabilities, member):
    return Status(kUnknownError, "has no such member variety")
  else:
    setattr(capabilities, member, option) 
    return Status(kOk)

def IgnoreCapability(option, capabilities):
  return Status(kOk)

def ParseTizenXwalk(option, capabilities):
  if type(option) != str and type(option) != unicode:
    return Status(kUnknownError, "must be 'host:port'")
  values = option.split(":")
  if len(values) != 2:
    return Status(kUnknownError, "must be 'host:port'")
  port = int(values[1])
  if port <= 0:
    return Status(kUnknownError, "port must be > 0")
  # TODO: I make debugger_address equal to "host:port" in string type
  capabilities.tizen_debugger_address = option
  return Status(kOk)

def ParseUseExistingBrowser(option, capabilities):
  if type(option) != str and type(option) != unicode:
    return Status(kUnknownError, "must be 'host:port'")
  values = option.split(":")
  if len(values) != 2:
    return Status(kUnknownError, "must be 'host:port'")
  port = int(values[1])
  if port <= 0:
    return Status(kUnknownError, "port must be > 0")
  # TODO: I make debugger_address equal to "host:port" in string type
  capabilities.debugger_address = option
  return Status(kOk)

def ParseFilePath(member, option, capabilities):
  if type(option) != str and type(option) != unicode:
    return Status(kUnknownError, "must be a string")
  elif not hasattr(capabilities, member):
    return Status(kUnknownError, "has no such member variety")
  else:
    setattr(capabilities, member, option) 
    return Status(kOk)

def ParseDict(member, option, capabilities):
  if type(option) != dict:
    return Status(kUnknownError, "must be a dictionary")
  elif not hasattr(capabilities, member):
    return Status(kUnknownError, "has no such member variety")
  else:
    setattr(capabilities, member, option) 
    return Status(kOk)

def ParseLogPath(option, capabilities):
  if type(option) != str and type(option) != unicode:
    return Status(kUnknownError, "must be a string")
  else:
    capabilities.log_path = option
    return Status(kOk)

def ParseExtensions(option, capabilities):
  if type(option) != list:
    return Status(kUnknownError, "must be a list")
  for extension in option:
    if type(extension) != str and type(extension) != unicode:
      return Status(StatusCode.kUnknownError, "each extension must be a base64 encoded string")
    capabilities.extensions.append(extension)
  return Status(kOk)

def IgnoreDeprecatedOption(option_name, option, capabilities):
  VLOG(2, "Deprecated xwalk option is ignored: " + option)
  return Status(kOk)

def ParseExcludeSwitches(option, capabilities):
  if type(option) != list:
    return Status(kUnknownError, "must be a list")
  for switch_name in option:
    if type(switch_name) != str and type(switch_name) != unicode:
      return Status(kUnknownError, "each switch to be removed must be a string")
    capabilities.exclude_switches.add(switch_name)
  return Status(kOk)

def ParseSwitches(option, capabilities):
  if type(option) != list:
    return Status(kUnknownError, "must be a list")
  for arg_string in option:
    if type(arg_string) != str and type(arg_string) != unicode:
      return Status(kUnknownError, "each argument must be a string")
    capabilities.switches.SetUnparsedSwitch(arg_string);
  return Status(kOk)

def ParseXwalkOptions(capability, capabilities):
  if type(capability) != dict:
    return Status(kUnknownError, "must be a dictionary")
  is_android = capability.has_key("androidPackage")
  is_existing = capability.has_key("debuggerAddress")
  is_tizen = capability.has_key("tizenDebuggerAddress")
  parser_map = {}
  # Ignore 'args', 'binary' and 'extensions' capabilities by default, since the
  # Java client always passes them.
  parser_map["args"] = Bind(IgnoreCapability)
  parser_map["binary"] = Bind(IgnoreCapability)
  parser_map["extensions"] = Bind(IgnoreCapability)
  if is_android:
    parser_map["androidActivity"] = Bind(ParseString, ["android_activity", capability.get("androidActivity"), capabilities])
    parser_map["androidDeviceSerial"] = Bind(ParseString, ["android_device_serial", capability.get("androidDeviceSerial"), capabilities])
    parser_map["androidPackage"] = Bind(ParseString, ["android_package", capability.get("androidPackage"), capabilities])
    parser_map["androidProcess"] = Bind(ParseString, ["android_process", capability.get("androidProcess"), capabilities])
    parser_map["androidUseRunningApp"] = Bind(ParseBoolean, ["android_use_running_app", capability.get("androidUseRunningApp"), capabilities])
    parser_map["args"] = Bind(ParseSwitches, [capability.get("args"), capabilities])
    parser_map["loadAsync"] = Bind(IgnoreDeprecatedOption, ["loadAsync", capability.get("loadAsync"), capabilities])
  elif is_tizen:
    parser_map["tizenDebuggerAddress"] = Bind(ParseTizenXwalk, [capability.get("tizenDebuggerAddress"), capabilities])
    parser_map["tizenAppId"] = Bind(ParseString, ["tizen_app_id", capability.get("tizenAppId"), capabilities])
    parser_map["tizenAppName"] = Bind(ParseString, ["tizen_app_name", capability.get("tizenAppName"), capabilities])
    parser_map["tizenDeviceSerial"] = Bind(ParseString, ["tizen_device_serial", capability.get("tizenDeviceSerial"), capabilities])
    parser_map["tizenUseRunningApp"] = Bind(ParseBoolean, ["tizen_use_running_app", capability.get("tizenUseRunningApp"), capabilities])
  elif is_existing:
    parser_map["debuggerAddress"] = Bind(ParseUseExistingBrowser, [capability.get("debuggerAddress"), capabilities])
  else:
    parser_map["args"] = Bind(ParseSwitches, [capability.get("args"), capabilities])
    parser_map["binary"] = Bind(ParseFilePath, ["binary", capability.get("binary"), capabilities])
    parser_map["detach"] = Bind(ParseBoolean, ["detach", capability.get("detach"), capabilities])
    parser_map["excludeSwitches"] = Bind(ParseExcludeSwitches, [capability.get("excludeSwitches"), capabilities])
    parser_map["extensions"] = Bind(ParseExtensions, [capability.get("extensions"), capabilities])
    parser_map["forceDevToolsScreenshot"] = Bind(ParseBoolean, ["force_devtools_screenshot", capability.get("forceDevToolsScreenshot"), capabilities])
    parser_map["loadAsync"] = Bind(IgnoreDeprecatedOption, ["loadAsync", capability.get("loadAsync"), capabilities])
    parser_map["localState"] = Bind(ParseDict, ["local_state", capability.get("localState"), capabilities])
    parser_map["logPath"] = Bind(ParseLogPath, [capability.get("logPath"), capabilities])
    parser_map["minidumpPath"] = Bind(ParseString, ["minidump_path", capability.get("minidumpPath"), capabilities])
    parser_map["prefs"] = Bind(ParseDict, ["prefs", capability.get("prefs"), capabilities])
  for key, value in capability.iteritems():
    if capability.get(key, None) != None:
      status = parser_map[key].Run()
      if status.IsError():
        VLOG(0, "error parse xwalk option: " + key)
        return Status(kUnknownError, "cannot parse " + key)
  return Status(kOk)

def ParseProxy(option, capabilities):
  proxy_dict = option
  if type(proxy_dict) != dict:
    return Status(kUnknownError, "must be a dictionary")
  proxy_type = proxy_dict.get("proxyType")
  #if type(proxy_type) != str and type(proxy_type) != unicode:
  if type(proxy_type) != str:
    return Status(kUnknownError, "'proxyType' must be a string")
  proxy_type.lower()
  if proxy_type == "direct":
    capabilities.switches.SetSwitch("no-proxy-server")
  elif proxy_type == "system":
    # Xwalk default.
    pass
  elif proxy_type == "pac":
    proxy_pac_url = proxy_dict.get("proxyAutoconfigUrl")
    #if type(proxy_pac_url) != str and type(proxy_pac_url) != unicode:
    if type(proxy_pac_url) != str:
      return Status(kUnknownError, "'proxyAutoconfigUrl' must be a string")
    capabilities.switches.SetSwitch("proxy-pac-url", proxy_pac_url)
  elif proxy_type == "autodetect":
    capabilities.switches.SetSwitch("proxy-auto-detect")
  elif proxy_type == "manual":
    proxy_servers_options = [
        ["ftpProxy", "ftp"], ["httpProxy", "http"], ["sslProxy", "https"]]
    option_value = ""
    proxy_servers = ""
    for item in proxy_servers_options:
      option_value = proxy_dict.get(item[0], None)
      if option_value == None:
        continue
      value = option_value
      if type(value) != str and type(value) != unicode:
        return Status(kUnknownError, item[0] + " must be a string")
      # Converts into Xwalk proxy scheme.
      # Example: "http=localhost:9000;ftp=localhost:8000".
      if proxy_servers:
        proxy_servers += ";"
      proxy_servers += item[1] + "=" + value

    proxy_bypass_list = ""
    option_value = proxy_dict.get("noProxy", None)
    if option_value != None:
      proxy_bypass_list = option_value
      #if type(proxy_bypass_list) != str and type(proxy_bypass_list) != unicode:
      if type(proxy_bypass_list) != str:
        return Status(kUnknownError, "'noProxy' must be a string")

    if not proxy_servers and not proxy_bypass_list:
      return Status(kUnknownError, "proxyType is 'manual' but no manual proxy capabilities were found")
    
    if proxy_servers:
      capabilities.switches.SetSwitch("proxy-server", proxy_servers)
    if proxy_bypass_list:
      capabilities.switches.SetSwitch("proxy-bypass-list", proxy_bypass_list)
  else:
    return Status(kUnknownError, "unrecognized proxy type:" + proxy_type)
  return Status(kOk)

class Capabilities(object):
  def __init__(self):
    self.android_activity = ""
    self.android_device_serial = ""
    self.android_package = ""
    self.android_process = ""
    self.android_use_running_app =False
    self.tizen_debugger_address = None
    self.tizen_app_id = ""
    self.tizen_app_name = ""
    self.tizen_device_serial = ""
    self.tizen_use_running_app = False
    self.binary = ""
    # If provided, the remote debugging address to connect to.
    self.debugger_address = None
    # Whether the lifetime of the started Xwalk browser process should be
    # bound to XwalkDriver's process. If true, Xwalk will not quit if
    # XwalkDriver dies.
    self.detach = False
    # Set of switches which should be removed from default list when launching
    # Xwalk.
    self.exclude_switches = set()
    self.extensions = []
    # True if should always use DevTools for taking screenshots.
    # This is experimental and may be removed at a later point.
    self.force_devtools_screenshot = False
    self.local_state = {}
    self.log_path = ""
    self.logging_prefs = {}
    # If set, enable minidump for xwalk crashes and save to this directory.
    self.minidump_path = ""
    self.prefs = {}
    self.switches = Switches()

  # Return true if existing host:port session is to be used.
  def IsExistingBrowser(self):
    return self.debugger_address > 0 and self.debugger_address < 65536

  # Return true if android package is specified.
  def IsAndroid(self):
    return self.android_package != ""

  # Return true if tizen package is specified.
  def IsTizen(self):
    return self.tizen_debugger_address > 0 and self.tizen_debugger_address < 65536

  def Parse(self, desired_caps):
    parser_map = {}
    if desired_caps.get("xwalkOptions", None) != None:
      parser_map["xwalkOptions"] = Bind(ParseXwalkOptions, [desired_caps["xwalkOptions"], self])
    if desired_caps.get("loggingPrefs", None) != None:
      parser_map["loggingPrefs"] = Bind(ParseLoggingPrefs, [desired_caps["loggingPrefs"], self])
    if desired_caps.get("proxy", None) != None:
      parser_map = Bind(ParseProxy, [desired_caps["proxy"], self])
    for label, cmd in parser_map.iteritems():
      status = cmd.Run()
      if status.IsError():
        return Status(kUnknownError, "cannot parse capability: " + label)
    return Status(kOk)

