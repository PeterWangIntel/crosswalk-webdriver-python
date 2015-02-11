__all__ = ["Adb"]

from status import *

""" protype of android device bridge which is served as an adb client, 
we move out the feature of manually setting adb server port. """
class Adb(object):
    
  def GetDevices(self, devices):
    return Status(kOk)
       
  def ForwardPort(self, device_serial, local_port, remote_abstract):
    return Status(kOk)

  def SetCommandLineFile(self, device_serial, command_line_file, exec_name, args):
    return Status(kOk)
    
  def CheckAppInstalled(self, device_serial, package):
    return Status(kOk)

  def ClearAppData(self, device_serial, package):
    return Status(kOk)

  def SetDebugApp(self, device_serial, package):
    return Status(kOk)

  def Launch(self, device_serial, package, activity):
    return Status(kOk)

  def ForceStop(self, device_serial, package):
    return Status(kOk)
        
  """ return status and pid<string> """
  def GetPidByName(self, device_serial, process_name):
    return (Status(kOk), "fake-pid")

  """ return status and response<string> """
  def ExecuteCommand(self, command):
    return (Status(kOk), "OKAY")

