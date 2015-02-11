__all__ = ["AdbImpl"]

import subprocess
import re
import time
from adb import Adb
from status import *
from base.thread_wrap import ExecuteGetResponse
from base.log import VLOG

class AdbImpl(Adb):
    
  def GetDevices(self, devices):
    devices[:] = []
    p = subprocess.Popen(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (res, errorMsg) = p.communicate()
    if errorMsg:
      return Status(kUnknownError, "Falied to get devices ")
    res = res.split('\n')
    # usually we target on only one device
    if len(res) == 4:
      devices.append(res[1].split('\t')[0])
      return Status(kOk)
    # maybe more than one devices
    elif len(res) > 4:
      for item in res[1:-2]:
        devices.append(item.split('\t')[0])
      return Status(kOk)
    else:
      return Status(kUnknownError, "Falied to get devices ")
       
  def ForwardPort(self, device_serial, local_port, remote_abstract):
    remote_abstract += "_devtools_remote"
    VLOG(1, "ForwardPort(local_port: %s, remote_abstract: %s)" % (local_port, remote_abstract)) 
    (status, res) = self.ExecuteCommand("adb -s " + device_serial + " forward tcp:" + local_port + \
                 " localabstract:" + remote_abstract)
    if status.IsError():
      return Status(kUnknownError, "Failed to forward ports to device " + device_serial + ": " + res)
    return status

  def SetCommandLineFile(self, device_serial, command_line_file, exec_name, args):
    return Status(kOk)
    
  def CheckAppInstalled(self, device_serial, package):
    VLOG(1, "CheckAppInstalled(package: %s)" % package)
    (status, res) = self.ExecuteCommand("adb -s " + device_serial + " shell pm path " + package)
    if status.IsError():
      return status
    if res.find("package") == -1:
      return Status(kUnknownError, package + " is not installed on device " + device_serial)
    return Status(kOk)

  def ClearAppData(self, device_serial, package):
    VLOG(1, "ClearAppData(package: %s)" % package)
    (status, res) = self.ExecuteCommand("adb -s " + device_serial + " shell pm clear " + package)
    if status.IsError():
      return status
    if res.find("Success") == -1:
      return Status(kUnknownError, "Failed to clear data for " + package + ": " + res)
    return Status(kOk)

  def SetDebugApp(self, device_serial, package):
    VLOG(1, "SetDebugApp(package: %s)" % package)
    (status, res) = self.ExecuteCommand("adb -s " + device_serial + " shell am set-debug-app --persistent " + package)
    if status.IsError():
      return status
    return Status(kOk)

  def Launch(self, device_serial, package, activity):
    VLOG(1, "Launch(package: %s, activity: %s)" % (package, activity))
    (status, res) = self.ExecuteCommand("adb -s " + device_serial + " shell am start -W -n " + package + "/" + activity + " -d data:,")
    if status.IsError():
      return status
    if res.find("Complete") == -1:
      return Status(kUnknownError, "Failed to start " + package + " on device " + device_serial + ": " + res)
    return Status(kOk)

  def ForceStop(self, device_serial, package):
    VLOG(1, "ForceStop(package: %s)" % package)
    (status, res) = self.ExecuteCommand("adb -s " + device_serial + " shell am force-stop " + package)
    if status.IsError():
      return status
    return Status(kOk)
        
  """ return status and pid<string> """
  def GetPidByName(self, device_serial, process_name):
    (status, res) = self.ExecuteCommand("adb -s " + device_serial + " shell ps")
    if status.IsError():
      return (status, "")
    patt = r'\w+\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\w+\s*\w+\s*\w\s*' + process_name
    matchObj = re.search(patt, res)
    if not matchObj:
      return (Status(kUnknownError, "Failed to get PID for the following process: " + process_name), "")
    pid = matchObj.groups()[0]
    VLOG(1, "GetPidByName(process_name: %s, pid: %s)" % (process_name, pid))
    return (Status(kOk), pid)

  """ return status and response<string> """
  def ExecuteCommand(self, command=""):
    # default command execute timeout 30 seconds
    return ExecuteGetResponse(command, 30).GetResponse()

