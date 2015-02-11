__all__ = ["LaunchXwalk"]

from browser.status import *
from browser.version import kMinimumSupportedXwalkBuildNo
from browser.version import GetMinimumSupportedXwalkVersion
from browser.xwalk_android_impl import XwalkAndroidImpl
from browser.devtools_http_client import DevToolsHttpClient
from browser.devtools_http_client import WebViewsInfo
from browser.devtools_http_client import WebViewInfo
from net.port_server import *
from base.log import VLOG
import time

kCommonSwitches = ["ignore-certificate-errors", "metrics-recording-only"]

def WaitForDevToolsAndCheckVersion(port, socket_factory, user_client):
  address = "127.0.0.1:" + port
  client = DevToolsHttpClient(address, socket_factory)
  #deadline = time.clock() + 20
  deadline = time.time() + 20
  #status = client.Init(deadline - time.clock())
  status = client.Init(deadline - time.time())
  #VLOG(0, "DevToolsHttpClient Init status: " + status.Message())
  if status.IsError():
    return status
  if int(client.build_no) < int(kMinimumSupportedXwalkBuildNo):
    return Status(kUnknownError, "Xwalk version must be >= " + GetMinimumSupportedXwalkVersion())
  #while time.clock() < deadline:
  while time.time() < deadline:
    views_info = WebViewsInfo()
    client.GetWebViewsInfo(views_info) 
    for item in views_info.views_info:
      if item.typer == WebViewInfo.kPage:
        user_client.Update(client)
        return Status(kOk)
    time.sleep(0.05)
  return Status(kUnknownError, "unable to discover open pages")

def LaunchExistingXwalkSession(socket_factory, \
                               capabilities, \
                               devtools_event_listeners, \
                               session):
  return Status(kOk)

def LaunchDesktopXwalk(port, \
                       port_reservation, \
                       socket_factory, \
                       capabilities, \
                       devtools_event_listeners, \
                       session):
  return Status(kOk)

def LaunchAndroidXwalk(port, \
                       port_reservation, \
                       socket_factory, \
                       capabilities, \
                       devtools_event_listeners, \
                       device_manager, \
                       session):
  status = Status(kOk)
  if not capabilities.android_device_serial:
    (status, device) = device_manager.AcquireDevice()
  else:
    (status, device) = device_manager.AcquireSpecificDevice(capabilities.android_device_serial)
  if status.IsError():
    return status
  switches = capabilities.switches
  for i in kCommonSwitches:
    switches.SetSwitch(i)
  switches.SetSwitch("disable-fre")
  switches.SetSwitch("enable-remote-debugging")
  status = device.SetUp(capabilities.android_package, \
                        capabilities.android_activity, \
                        capabilities.android_process, \
                        switches.ToString(), \
                        capabilities.android_use_running_app, \
                        port)
  if status.IsError():
    device.TearDown()
    return status
  devtools_client = DevToolsHttpClient("fake-url", None)
  status = WaitForDevToolsAndCheckVersion(port, socket_factory, devtools_client)
  if status.IsError():
    VLOG(0, "failed WaitForDevToolsAndCheckVersion: " + status.Message())
    device.TearDown()
    return status
  session.xwalk = XwalkAndroidImpl(devtools_client, \
                                   devtools_event_listeners, \
                                   port_reservation, \
                                   device)
  return Status(kOk)

def LaunchTizenXwalk(port, \
                     port_reservation, \
                     socket_factory, \
                     capabilities, \
                     devtools_event_listeners, \
                     device_manager, \
                     session):
  return Status(kOk)

def LaunchXwalk(socket_factory, \
                device_manager, \
                port_server, \
                port_manager, \
                capabilities, \
                devtools_event_listeners, \
                session):
  if capabilities.IsExistingBrowser():
    return LaunchExistingXwalkSession(socket_factory, capabilities, devtools_event_listeners, session)
  if port_server != None:
    (port_status, port, port_reservation) = port_server.ReservePort()
  else:
    (port_status, port, port_reservation) = port_manager.ReservePort()
  if port_status.IsError():
    return Status(kUnknownError, "cannot reserve port for Xwalk: " + port_status.Message())
  if capabilities.IsAndroid():
    return LaunchAndroidXwalk(port, port_reservation, socket_factory, capabilities, devtools_event_listeners, device_manager, session)
  elif capabilities.IsTizen():
    return LaunchTizenXwalk(port, port_reservation, socket_factory, capabilities, devtools_event_listeners, device_manager, session)
  else:
    return LaunchDesktopXwalk(port, port_reservation, socket_factory, capabilities, devtools_event_listeners, session)

