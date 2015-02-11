__all__ = ["ThreadWrap", "ExecuteGetResponse"]

import threading
import subprocess
import time
import Queue
import sys
import re
from browser.status import *
from log import VLOG

""" wrapper of basic thread where commands enqueued should run on same thread with 
same session id for avoiding race condition. 
  since it uses condition var to sync the timeline between threads, it's thread safety.
  ThreadWrap is truly run by ThreadWrap.start(), and then it in sequence runs its 
task(aka, command), it does not quit until receive quit command wrapped in task. 
Finally you can call its you can dynamically append new task by ThreadWrap.PostTask(cmd) """

class ThreadWrap(threading.Thread):

  def __init__(self, condition, session_id, session):
    threading.Thread.__init__(self, name=session_id)
    # use to sync between main thread and itself
    self.condition = condition
    # use to control its own state
    self.queue = Queue.Queue()
    self.session = session
    # tracing shared vars by any command
    self.status = Status(kOk)
    self.value = {}
    # delay enough time to make sure its parents thread acquire the condition first, so
    # that parent thread can add itself to notify table
    self.is_ready = False
  
  def run(self):
    while True:
      if not self.is_ready:
        continue
      if self.queue:
        cmd = self.queue.get()
        self.status = cmd.Run()
        if hasattr(cmd, 'is_send_func_'):
          # since in low level, switching between threads makes socket reset to NoneType, we
          # use a condition var to sync between threads to make safety of socket
          self.condition.acquire()
          self.condition.notify()
          self.condition.release()
        if hasattr(cmd, 'is_quit_func_'):
          # is_quit_func_ is a dynamically attr where it is easily glued to cmd by 
          # cmd.is_quit_func_ = True, when run() notice the attr of cmd, the thread 
          # wrapper is finaly quit
          return
      else:
        # block itself until waked by self.PostTask()
        # release the ownership of cpu
        time.sleep(0.05)

  def PostTask(self, cmd):
    self.queue.put(cmd)
    return

""" since python' subprocess module does not support manual timeout setting. 
This class binds the wanted commands and post the task to another thread which
can be under control in timeout setting calling thread.join(timeout) """

class ExecuteGetResponse(object):

  def __init__(self, cmd="", timeout=3):
    self.cmd = cmd
    self.timeout = timeout
    self.process = None
    self.stdout = ""
    self.stderr = ""
    self.is_timeout = False
    self.Run()

  def Task(self):
    self.process = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (self.stdout, self.stderr) = self.process.communicate()
    return

  def Run(self):
    thread = threading.Thread(target=self.Task)
    thread.start()
    thread.join(self.timeout)
    if thread.is_alive():
      self.is_timeout = True
      self.process.terminate()
      thread.join()
    return

  # return status and response<string> 
  def GetResponse(self):
    # handle timeout error
    if self.is_timeout:
      msg = "Xdb command timed out after %s seconds" % str(self.timeout)
      return (Status(kTimeout, msg), "")
    # handle command execute shell-like error, etc. command unregconize or spelled error
    if self.stderr:
      VLOG(3, "Xdb: %s - %s" % (self.cmd, self.stderr))
      return (Status(kUnknownError, "Failed to run Xdb command, is the Xdb server running?"), "")
    # handle adb execute error
    matchObj = re.search(r'error', self.stdout, re.I)
    if matchObj:
      VLOG(3, "Xdb: %s - %s" % (self.cmd, self.stdout))
      return (Status(kUnknownError, "Failed to run Xdb command, detailed message:" + self.stdout), "")
    return (Status(kOk), self.stdout)
    
