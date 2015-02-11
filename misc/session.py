__all__ = ["Session"]

import time
from basic_types import WebPoint
from capabilities import Capabilities
from geoposition import Geoposition
from browser.status import *
from browser.xwalk import Xwalk
from base.log import VLOG

class FrameInfo(object):

  def __init__(self, parent_frame_id, frame_id, xwalkdriver_frame_id):
    self.parent_frame_id = parent_frame_id
    self.frame_id = frame_id
    self.xwalkdriver_frame_id = xwalkdriver_frame_id

  def Update(self, other):
    self.parent_frame_id = other.parent_frame_id
    self.frame_id = other.frame_id
    self.xwalkdriver_frame_id = other.xwalkdriver_frame_id

class Session(object):
  # set default page load time out 5 minutes
  kDefaultPageLoadTimeout = 300

  def __init__(self, sid, xwalk=Xwalk()):
  # rename id to sid avoid disturbing key word
    self.sid = sid
    self.xwalk = xwalk
    self.quit = False
    self.detach = False
    self.force_devtools_screenshot = False
    self.sticky_modifiers = 0
    self.mouse_position = WebPoint(0, 0)
    self.page_load_timeout = Session.kDefaultPageLoadTimeout
    self.window = ""
    # List of |FrameInfo|s for each frame to the current target frame from the
    # first frame element in the root document. If target frame is window.top,
    # this list will be empty.
    self.frames = [] 
    # implicit_wait mill seconds
    self.implicit_wait = None
    self.script_timeout = None
    self.prompt_text = ""
    self.overridden_geoposition = None
    # Logs that populate from DevTools events.
    self.devtools_logs = []
    self.driver_log = None
    # TODO:implement <base::ScopedTempDir>
    self.temp_dir = None
    self.capabilities = {}
  
  def Update(self, other):
    self.sid = other.sid
    self.xwalk = other.xwalk
    self.quit = other.quit
    self.detach = other.detach
    self.force_devtools_screenshot = other.force_devtools_screenshot
    self.sticky_modifiers = other.sticky_modifiers
    self.mouse_position = other.mouse_position
    self.page_load_timeout = other.page_load_timeout
    self.window = other.window
    self.frames = other.frames
    self.implicit_wait = other.implicit_wait
    self.script_timeout = other.script_timeout
    self.prompt_text = other.prompt_text
    self.overridden_geoposition = other.overridden_geoposition
    self.devtools_logs = other.devtools_logs
    self.driver_log = other.driver_log
    self.temp_dir = other.temp_dir
    self.capabilities = other.capabilities

  def GetTargetWindow(self, web_view):
    if self.xwalk == None:
      return Status(kNoSuchWindow, "no xwalk started in this session")
    status = self.xwalk.GetWebViewById(self.window, web_view)
    #VLOG(0, "after GetWebViewById: " + status.Message()) 
    if status.IsError():
      status = Status(kNoSuchWindow, "target window already closed")
    return status

  def SwitchToTopFrame(self):
    self.frames = []
    return

  def SwitchToSubFrame(self, frame_id, xwalkdriver_frame_id):
    parent_frame_id = ""
    if self.frames:
      parent_frame_id = self.frames[-1]
    self.frames.append(FrameInfo(parent_frame_id, frame_id, xwalkdriver_frame_id))
    return
    
  def GetCurrentFrameId(self):
    if not self.frames:
      return ""
    return self.frames[-1].frame_id

  def GetAllLogs(self): 
    pass
    
