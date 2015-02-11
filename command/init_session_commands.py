__all__ = ["GenerateId", \
           "InitSessionParams", \
           "ExecuteInitSession", \
           "ExecuteQuit", \
           "ExecuteGetStatus"]

import random
import os
from misc.capabilities import Capabilities
from misc.xwalk_launcher import LaunchXwalk
from browser.status import *
from browser.version import kXwalkDriverVersion
from base.log import VLOG

# generate session id
def GenerateId():
  rand = hex(random.randrange(0, 2**64))
  if rand.endswith('L'):
    msb = rand[2:-1]
  else:
    msb = rand[2:]
  rand = hex(random.randrange(0, 2**64))
  if rand.endswith('L'):
    lsb = rand[2:-1]
  else:
    lsb = rand[2:]
  sessionId = msb + lsb    
  return sessionId

class InitSessionParams(object):

  def __init__(self, socket_factory, device_manager, port_server, port_manager):
    self.socket_factory = socket_factory
    self.device_manager = device_manager
    self.port_server = port_server
    self.port_manager = port_manager

def _CreateCapabilities(xwalk):
  caps = {}
  caps["browserName"] = "xwalk"
  caps["version"] = "webview"
  caps["version"] = xwalk.GetVersion()
  caps["xwalk.xwalkdriverVersion"] = kXwalkDriverVersion
  caps["platform"] = xwalk.GetOperatingSystemName()
  caps["platform"] = "ANDROID"
  caps["javascriptEnabled"] = True
  caps["takesScreenshot"] = True
  caps["takesHeapSnapshot"] = True
  caps["handlesAlerts"] = True
  caps["databaseEnabled"] = False
  caps["locationContextEnabled"] = True
  caps["applicationCacheEnabled"] = False
  caps["browserConnectionEnabled"] = False
  caps["cssSelectorsEnabled"] = True
  caps["webStorageEnabled"] = True
  caps["rotatable"] = False
  caps["acceptSslCerts"] = True
  caps["nativeEvents"] = True
  xwalk_caps = {}
  if xwalk.GetAsDesktop():
    xwalk_caps["userDataDir"] = xwalk.GetAsDesktop().command().GetSwitchValueNative("user-data-dir")
  caps["xwalk"] = xwalk_caps
  return caps

def _InitSessionHelper(bound_params, session, params, value):
  #TODO
  #session->driver_log.reset(
  #    new WebDriverLog(WebDriverLog::kDriverType, Log::kAll));
  desired_caps = params.get("desiredCapabilities")
  if type(desired_caps) != dict:
    return Status(kUnknownError, "cannot find dict 'desiredCapabilities'")
  capabilities = Capabilities() 
  status = capabilities.Parse(desired_caps)
  if status.IsError():
    return status
  #VLOG(0, "after parse capabilities: " + status.Message())
  #TODO
  #Log::Level driver_level = Log::kWarning;
  #if (capabilities.logging_prefs.count(WebDriverLog::kDriverType))
  #  driver_level = capabilities.logging_prefs[WebDriverLog::kDriverType];
  #session->driver_log->set_min_level(driver_level);

  # Create Log's and DevToolsEventListener's for ones that are DevTools-based.
  # Session will own the Log's, Xwalk will own the listeners.
  devtools_event_listeners = []
  #TODO
  #status = CreateLogs(capabilities,
  #                    &session->devtools_logs,
  #                    &devtools_event_listeners);
  #if (status.IsError())
  #  return status;
  status = LaunchXwalk(bound_params.socket_factory, \
                       bound_params.device_manager, \
                       bound_params.port_server, \
                       bound_params.port_manager, \
                       capabilities, \
                       devtools_event_listeners, \
                       session)
  #VLOG(0, "after launchxwalk: " + status.Message())
  if status.IsError():
    return status
  web_view_ids = []
  status = session.xwalk.GetWebViewIds(web_view_ids)
  if status.IsError():
    VLOG(0, "session.xwalk.GetWebViewIds: " + status.Message())
    return status
  if not web_view_ids:
    VLOG(0, "web_view_ids is []: " + status.Message())
    return Status(kUnknownError, "unable to discover open window in xwalk")
  VLOG(0, "web_view_ids is: " + str(web_view_ids))
  session.window = web_view_ids[0]
  session.detach = capabilities.detach
  session.force_devtools_screenshot = capabilities.force_devtools_screenshot
  session.capabilities = _CreateCapabilities(session.xwalk)
  value.clear()
  value.update(session.capabilities)
  return Status(kOk)

def ExecuteInitSession(bound_params, session, params, value):
  status = _InitSessionHelper(bound_params, session, params, value);
  if status.IsError():
    session.quit = True
  return status

def ExecuteQuit(allow_detach, session, params, value): 
  if allow_detach and session.detach:
    return Status(kOk)
  else:
    return session.xwalk.Quit()

def ExecuteGetStatus(value):
  build = {}
  build["version"] = "alpha"
  os_uname = os.uname() # Operating System Name
  os_info = {}
  os_info["name"] = os_uname[0] # Operating System Name
  os_info["version"] = os_uname[2] # Operating System Version
  os_info["arch"] =  os_uname[-1] # Operating System Architecture
  info = {}
  info["build"] = build
  info["os"] = os_info
  value.clear()
  value.update(info)
  return Status(kOk)

