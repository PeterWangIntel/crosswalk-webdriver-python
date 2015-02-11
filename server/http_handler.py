import BaseHTTPServer
import re
import time
import threading
import json
import yaml
import os
from browser.device_manager import DeviceManager
from browser.adb_impl import AdbImpl
from browser.sdb_impl import SdbImpl
from browser.status import *
from command.init_session_commands import *
from command.window_commands import ExecuteWindowCommand
from command.session_commands import ExecuteSessionCommand
from command.element_commands import ExecuteElementCommand
from command.command_mapping import *
from misc.session import Session
from base.bind import Bind
from base.log import VLOG
from base.thread_wrap import ThreadWrap
from net.port_server import PortManager
from net.http_error_code import *
from net.websocket_factory import WebsocketFactory

# inner complement of Http request handler
class XwalkHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):

  def __init__(self, port, url_base, target, port_server, *args):
    self.port_ = port
    self.url_base_ = url_base
    self.port_server_ = port_server
    self.socket_factory_ = WebsocketFactory()
    self.port_manager_ = PortManager(12000, 13000)

    # determine type of device_manager according to device_os, so whenever meet
    # judge logic, you can call isinstance(device_manager.xdb_, AdbImpl)
    if target == "android":
      self.device_manager_ = DeviceManager(AdbImpl())
    else:
      self.device_manager_ = DeviceManager(SdbImpl())
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args)

  def PrepareResponse(self, trimmed_path, status, value, session_id):
    response = self.PrepareResponseHelper(trimmed_path, status, value, session_id)
    # VLOG(0, "SendTo Selenium: " + str(response))
    self.send_response(response["code"])
    for header_item in response["headers"]:
      self.send_header(header_item[0], header_item[1])
    self.end_headers()
    self.wfile.write(response["body"])
    return Status(kOk)

  def PrepareResponseHelper(self, trimmed_path, status, value, session_id):
    if status.Code() == kUnknownCommand:
      response = {"code": HTTP_NOT_IMPLEMENTED, 
                  "headers": [["", ""],], 
                  "body": "unimplemented command: " + trimmed_path}
      return response

    if trimmed_path == "/status" and status.IsOk():
      response = {}
      response["code"] = HTTP_OK
      response["headers"] = [["Content-Type", "application; charset=utf-8"],]
      response["body"] = value
      return response

    if trimmed_path == "/session" and status.IsOk():
    # Creating a session involves a HTTP request to /session, which is
    # supposed to redirect to /session/:sessionId, which returns the
    # session info.
      body_params = {}
      body_params["status"] = status.Code()
      body_params["sessionId"] = session_id
      body_params["value"] = value
      response = {"code": HTTP_OK, 
                  "headers": [["Content-Location", self.url_base_ + "session/" + session_id],],
                  "body": json.dumps(body_params)}
      return response
    # handle error status of executing commmand
    elif status.IsError():
      full_status = status
      full_status.AddDetails("Driver info: xwalkdriver=" + kXwalkDriverVersion + \
                             ",platform=" + os.uname()[0] + " " + os.uname()[2] + " " + os.uname()[-1])
      value.clear()
      value.update({"message": full_status.Message()})

    # handle the others successful command
    body_params = {}
    body_params["status"] = status.Code()
    body_params["value"] = value.get("value", value)
    body_params["sessionId"] = session_id
    body_params_str = json.dumps(body_params)
    response = {}
    response["code"] = HTTP_OK
    response["headers"] = [["Content-Type", "application; charset=utf-8"],]
    response["body"] = body_params_str
    return response

  def ExecuteCreateSession(self):
    # init session command, capabilities is located in content
    params = {}
    varLen = int(self.headers['Content-Length'])
    content = self.rfile.read(varLen)
    # we focus on ascii not unicode
    params = yaml.load(content)
    # Create a new session
    new_id = GenerateId()
    session = Session(new_id)
    # Create a condition for main thread to wait for...
    condition = threading.Condition()
    target_thread = ThreadWrap(condition, new_id, session)
    # use to send response message to selenium side
    response_cmd = Bind(self.PrepareResponse, ["/session", target_thread.status, target_thread.value, new_id])
    # glue a dynamic attr to response command
    response_cmd.is_send_func_ = True
    # prepare init session command
    bound_params = InitSessionParams(self.socket_factory_, \
                                     self.device_manager_, \
                                     self.port_server_, \
                                     self.port_manager_)
    init_session_cmd = Bind(ExecuteInitSession, [bound_params, session, params, target_thread.value])
    target_thread.PostTask(init_session_cmd)
    target_thread.PostTask(response_cmd)
    # run the new thread
    try:
      target_thread.start()
    except:
      response_cmd = Bind(self.PrepareResponse, ["/session", Status(kUnknownError, "failed to start a thread for the new session"), {}, ""])
      response_cmd.Run()
      return Status(kUnknownError, "failed to start a thread for new session")
    # use condition lock to make sure current thread blocks until the child-thread finishes execute send function
    condition.acquire()
    target_thread.is_ready = True
    condition.wait()
    condition.release()
    return Status(kOk)

  def ExecuteDeleteSession(self):
    matchObj = re.match(r'/session/([a-f0-9]+)$', self.path)
    target_session_id = matchObj.groups()[0]
    target_thread = None
    # hit the target thread
    for item in threading.enumerate():
      if item.name == target_session_id:
        target_thread = item
        break
    if target_thread == None:
      status = Status(kNoSuchSession)
      VLOG(3, status.Message())
      return status
    # quit relative xwalk impl
    quit_session_cmd = Bind(ExecuteQuit, [False, target_thread.session, {}, {}])
    # send response
    response_cmd = Bind(self.PrepareResponse, [self.path, Status(kOk), {}, target_session_id])
    response_cmd.is_send_func_ = True
    # quit thread
    quit_thread_cmd = Bind(Bind._RunNothing)
    quit_thread_cmd.is_quit_func_ = True
    target_thread.PostTask(quit_session_cmd)
    target_thread.PostTask(response_cmd)
    # use condition lock to make sure current thread blocks until the child-thread finishes execute send function
    target_thread.condition.acquire()
    target_thread.condition.wait()
    target_thread.condition.release()
    target_thread.PostTask(quit_thread_cmd)
    return Status(kOk)

  def SessionCommandHandler(self):
    execute_cmd = None
    # parse what kind of session command
    for key, value in SessionCommandMapping.iteritems():
      matchObj = re.match(key, self.path)
      if matchObj:
        execute_cmd = SessionCommandMapping[key].get(self.command, None)
        # ensure the command is valid
        if execute_cmd != None:
          # handle /status and /sessions
          if self.path == '/status':
            value = {}
            execute_cmd.Update([value])
            execute_cmd.Run()
            return self.PrepareResponse(self.path, Status(kOk), value, "ignore")
          elif self.path == '/sessions':
            return
          else: 
            target_session_id = matchObj.groups()[0]
          break
    # ignore invalid command
    if execute_cmd == None:
      return Status(kUnknownCommand, "invalid or unimplement session command from selenium")
    # handle command
    # hit the target thread
    for item in threading.enumerate():
      if item.name == target_session_id:
        target_thread = item
        break
    if target_thread == None:
      return Status(kNoSuchSession)
    # extract the params from selenium
    params = {}
    try:
      varLen = int(self.headers['Content-Length'])
    except:
      # in case of no such header option
      varLen = 0
    if varLen:
      content = self.rfile.read(varLen)
      #params = json.loads(content)
      params = yaml.load(content)
    # dynamic reset parameters of session command
    session_cmd = Bind(ExecuteSessionCommand, [execute_cmd, target_thread.session, params, target_thread.value])
    # prepare response to selenium command
    response_cmd = Bind(self.PrepareResponse, [self.path, target_thread.status, target_thread.value, target_session_id])
    response_cmd.is_send_func_ = True
    target_thread.PostTask(session_cmd)
    target_thread.PostTask(response_cmd)
    # use condition lock to make sure current thread blocks until the child-thread finishes execute send function
    target_thread.condition.acquire()
    target_thread.condition.wait()
    target_thread.condition.release()
    return Status(kOk)
    
  def WindowCommandHandler(self):
    execute_cmd = None
    # parse what kind of window command
    for key, value in WindowCommandMapping.iteritems():
      matchObj = re.match(key, self.path)
      if matchObj:
        execute_cmd = WindowCommandMapping[key].get(self.command, None)
        # ensure the command is valid
        if execute_cmd != None:
          target_session_id = matchObj.groups()[0]
          break
    # ignore invalid command
    if execute_cmd == None:
      return Status(kUnknownCommand, "invalid or unimplement window command from selenium")
    # handle command
    # hit the target thread
    for item in threading.enumerate():
      if item.name == target_session_id:
        target_thread = item
        break
    if target_thread == None:
      return Status(kNoSuchSession)
    # extract the params from selenium
    params = {}
    try:
      varLen = int(self.headers['Content-Length'])
    except:
      # in case of no such header option
      varLen = 0
    if varLen:
      content = self.rfile.read(varLen)
      #params = json.loads(content)
      params = yaml.load(content)
    # make up window command
    window_cmd = Bind(ExecuteWindowCommand, [execute_cmd, target_thread.session, params, target_thread.value])
    # prepare response to selenium command
    response_cmd = Bind(self.PrepareResponse, [self.path, Status(kOk), target_thread.value, target_session_id])
    response_cmd.is_send_func_ = True
    target_thread.PostTask(window_cmd)
    target_thread.PostTask(response_cmd)
    # use condition lock to make sure current thread blocks until the child-thread finishes execute send function
    target_thread.condition.acquire()
    target_thread.condition.wait()
    target_thread.condition.release()
    return Status(kOk)

  def ElementCommandHandler(self):
    execute_cmd = None
    element_id = None
    # for those special commands which own more than 2 params packed in url request
    # we need extrally store them
    # /session/:sessionId/element/:id/attribute/:name
    # /session/:sessionId/element/:id/equals/:other
    # /session/:sessionId/element/:id/css/:propertyName
    extra_url_params = None
    # parse what kind of element command
    for key, value in ElementCommandMapping.iteritems():
      matchObj = re.match(key, self.path)
      if matchObj:
        execute_cmd = ElementCommandMapping[key].get(self.command, None)
        # ensure the command is valid
        if execute_cmd != None:
          target_session_id = matchObj.groups()[0]
          element_id = matchObj.groups()[1]
          if len(matchObj.groups()) == 3:
            extra_url_params = matchObj.groups()[2]
          break
    # ignore invalid command
    if execute_cmd == None:
      return Status(kUnknownCommand, "invalid or unimplement window command from selenium")
    # handle command
    # hit the target thread
    for item in threading.enumerate():
      if item.name == target_session_id:
        target_thread = item
        break
    if target_thread == None:
      return Status(kNoSuchSession)
    # extract the params from selenium
    params = {}
    try:
      varLen = int(self.headers['Content-Length'])
    except:
      # in case of no such header option
      varLen = 0
    if varLen:
      content = self.rfile.read(varLen)
      params = yaml.load(content)
    # don't forget to insert extra_url_params
    params["extra_url_params"] = extra_url_params
    # make up element command
    element_cmd = Bind(ExecuteElementCommand, [execute_cmd, element_id, target_thread.session, params, target_thread.value])
    # prepare response to selenium command
    response_cmd = Bind(self.PrepareResponse, [self.path, Status(kOk), target_thread.value, target_session_id])
    response_cmd.is_send_func_ = True
    target_thread.PostTask(element_cmd)
    target_thread.PostTask(response_cmd)
    # use condition lock to make sure current thread blocks until the child-thread finishes execute send function
    target_thread.condition.acquire()
    target_thread.condition.wait()
    target_thread.condition.release()
    return Status(kOk)

  def do_POST(self):
    VLOG(1, "%s : %s" % (self.command, self.path))
    if re.match(r'/session$', self.path):
      return self.ExecuteCreateSession()
    else:
      self.SessionCommandHandler()
      self.WindowCommandHandler()
      self.ElementCommandHandler()
    
  def do_GET(self):
    VLOG(1, "%s : %s" % (self.command, self.path))
    self.SessionCommandHandler()
    self.WindowCommandHandler()
    self.ElementCommandHandler()
        
  def do_DELETE(self):
    VLOG(1, "%s : %s" % (self.command, self.path))
    if re.match(r'/session/([a-f0-9]+)$', self.path):
      self.ExecuteDeleteSession()
    else:
      self.SessionCommandHandler()
      self.WindowCommandHandler()
      self.ElementCommandHandler()

""" interface of XwalkHttpHandler for extending BaseHTTPRequestHandler """
def XwalkHttpHandlerWrapper(port, url_base, target, port_server):
  return lambda *args: XwalkHttpHandler(port, url_base, target, port_server, *args)

