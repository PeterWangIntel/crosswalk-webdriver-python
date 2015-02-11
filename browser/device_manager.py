__all__ = ["DeviceManager"]

from adb_impl import AdbImpl
from android_device import AndroidDevice
from status import *
from base.log import VLOG

class DeviceManager(object):

  def __init__(self, xdb):
    self.xdb = xdb
    self.active_devices = []

  # Returns a device which will not be reassigned during its lifetime.
  def AcquireDevice(self):
    devices = []
    status = self.xdb.GetDevices(devices)
    if status.IsError():
      return (status, None)
    if not devices:
      return (Status(kUnknownError, "There are no devices online"), None)
    status = Status(kUnknownError, "All devices are in use (" + str(len(devices)) + " online)")
    for it in devices:
      if self.IsDeviceLocked(it):
        self.active_devices.remove(it)
        device = self.LockDevice(it)
        status = Status(kOk)
        break
      else:
        device = self.LockDevice(it)
        status = Status(kOk)  
        break
    return (status, device)

  # Returns a device with the same guarantees as AcquireDevice, but fails
  # if the device with the given serial number is not avaliable.
  def AcquireSpecificDevice(self, device_serial):
    devices = []
    status = self.xdb.GetDevices(devices)
    if status.IsError():
      return (status, None)
    if device_serial not in devices:
      return (Status(kUnknownError, "Device " + device_serial + " is not online"), None)
    if self.IsDeviceLocked(device_serial):
      status = (Status(kUnknownError, "Device " + device_serial + " is already in use"), None)
    else:
      device = self.LockDevice(device_serial)
      status = Status(kOk)
    return (status, device)

  def ReleaseDevice(self, device_serial):
    self.active_devices.remove(device_serial)
    return

  def LockDevice(self, device_serial):
    self.active_devices.append(device_serial)
    # before following process, xdb'type must be choiced outside
    if isinstance(self.xdb, AdbImpl):
      return AndroidDevice(device_serial, self.xdb, self.ReleaseDevice)
    else:
      return AndroidDevice(device_serial, self.xdb, self.ReleaseDevice)

  def IsDeviceLocked(self, device_serial):
    return device_serial in self.active_devices

