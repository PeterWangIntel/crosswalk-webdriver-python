__all__ = ["HeapSnapshotTaker"]

from devtools_event_listener import DevToolsEventListener
from status import *
from base.log import VLOG

# Take the heap snapshot.
class HeapSnapshotTaker(DevToolsEventListener):

  def __init__(self, client):
    self.client = client
    self.client.AddListener(self)
    self.snapshot_uid = -1
    self.snapshot = ""

  # return status and snapshot<value>
  def TakeSnapshot(self):
    snapshot = None
    status1 = self._TakeSnapshotInternal()
    params = {}
    status2 = self.client.SendCommand("Debugger.disable", params)
    status3 = Status(kOk)
    if self.snapshot_uid != -1:
    # Clear the snapshot cached in xwalk.
      status3 = self.client.SendCommand("HeapProfiler.clearProfiles", params)
    status4 = Status(kOk)
    if status1.IsOk() and status2.IsOk() and status3.IsOk():
      try:
        snapshot = json.loads(self.snapshot)
      except:
        status4 = Status(kUnknownError, "heap snapshot not in JSON format")
    self.snapshot_uid = -1
    self.snapshot = ""
    if status1.IsError():
      return (status1, snapshot)
    elif status2.IsError():
      return (status2, snapshot)
    elif status3.IsError():
      return (status3, snapshot)
    else:
      return (status4, snapshot)

  # Overridden from DevToolsEventListener:
  def OnEvent(self, client, method, params):
    if method == "HeapProfiler.addProfileHeader":
      #self.snapshot_uid = params.get("header.uid", None)
      self.snapshot_uid = params["header"].get("uid", None)
      if self.snapshot_uid != -1:
        VLOG(3, "multiple heap snapshot triggered")
      #TODO: header.uid format
      elif type(params["header"].get("uid")) != int:
        return Status(kUnknownError, "HeapProfiler.addProfileHeader has invalid 'header.uid'")
    elif method == "HeapProfiler.addHeapSnapshotChunk":
      uid = -1
      uid = params.get("uid")
      if type(uid) != int:
        return Status(kUnknownError, "HeapProfiler.addHeapSnapshotChunk has no 'uid'")
      elif uid == self.snapshot_uid:
        chunk = params.get("chunk")
        if type(chunk) != str:
          return Status(kUnknownError, "HeapProfiler.addHeapSnapshotChunk has no 'chunk'")
        self.snapshot += chunk
      else:
        VLOG(3, "expect chunk event uid " + self.snapshot_uid + ", but got " + str(uid))
    return Status(kOk)

  def _TakeSnapshotInternal(self):
    if self.snapshot_uid != -1:
      return Status(kUnknownError, "unexpected heap snapshot was triggered")
    params = {}
    kMethods = ["Debugger.enable", "HeapProfiler.collectGarbage", "HeapProfiler.takeHeapSnapshot"]
    for i in kMethods:
      status = self.client.SendCommand(i, params)
      if status.IsError():
        return status
    if self.snapshot_uid == -1:
      return Status(kUnknownError, "failed to receive snapshot uid")
    uid_params = {}
    uid_params["uid"] = self.snapshot_uid
    status = self.client.SendCommand("HeapProfiler.getHeapSnapshot", uid_params)
    if status.IsError():
      return status
    return Status(kOk)

