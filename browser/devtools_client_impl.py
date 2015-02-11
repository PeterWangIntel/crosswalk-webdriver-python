__all__ = ["DevToolsClientImpl"]

import copy
import json
import yaml
import time
from status import *
from devtools_client import DevToolsClient
from base.bind import Bind
from base.log import VLOG
from net.websocket_factory import WebsocketFactory
from third_party.websocket_client.websocket import WebSocketConnectionClosedException
from third_party.websocket_client.websocket import WebSocketTimeoutException

# InspectorMessageType
kEventMessageType = 0
kCommandResponseMessageType = 1

kInspectorContextError = "Execution context with given id not found."

class InspectorMessageType(object):

  def __init__(self, typer=0):
    self.typer = typer

class InspectorEvent(object):

  def __init__(self, method="", params={}):
    self.method = method
    self.params = params

class InspectorCommandResponse(object):

  def __init__(self, sid="", error="", result={}):
    self.sid = sid
    self.error = error
    self.result = result

# ResponseState
# The client is waiting for the response.
kWaiting = 0
# The command response will not be received because it is blocked by an
# alert that the command triggered.
kBlocked = 1
# The client no longer cares about the response.
kIgnored = 2
# The response has been received.
kReceived = 3

class ResponseInfo(object):

  def __init__(self, method=""):
    self.method = method
    self.state = kWaiting
    self.response = InspectorCommandResponse()

  def Update(self, other):
    self.method = other.method
    self.state = other.state
    self.response = other.response

def _ParseInspectorError(error_json):
  error_dict = yaml.load(error_json)
  if type(error_dict) != dict:
    return Status(kUnknownError, "inspector error with no error_message")
  error_message = error_dict.get("message")
  if type(error_message) == str and error_message == kInspectorContextError:
    return Status(kNoSuchExecutionContext)
  return Status(kUnknownError, "unhandled inspector error: " + error_json) 

class _ScopedIncrementer(object):

  def __init__(self, count):
    # focus: count must be mutable object
    self.reference = count
    self.reference[0] += 1

  def __del__(self):
    self.reference[0] -= 1

# return status and is_condition_met 
def _ConditionIsMet(): 
  return (Status(kOk), True)

def _ParseInspectorMessage(message, expected_id, message_type, event, command_response):
  message_dict = yaml.load(message)
  if message == "" or type(message_dict) != dict:
    return False
  if not message_dict.has_key("id"):
    method = message_dict.get("method")
    if type(method) != str:
      return False
    params = message_dict.get("params", {})
    message_type.typer = kEventMessageType
    event.method = method
    event.params = params
    return True
  elif type(message_dict["id"]) == int:
    sid = message_dict["id"]
    unscoped_error = message_dict.get("error")
    unscoped_result = message_dict.get("result")
    if type(unscoped_error) != dict and type(unscoped_result) != dict:
      return False
    message_type.typer = kCommandResponseMessageType
    command_response.sid = sid
    if unscoped_result:
      command_response.result = unscoped_result
    else:
      command_response.error = json.dumps(unscoped_error)
    return True
  return False

class DevToolsClientImpl(DevToolsClient):

  def __init__(self, factory, url, sid, frontend_closer_func, parser_func=Bind(_ParseInspectorMessage)):
    DevToolsClient.__init__(self)
    self.socket = factory.create_connection()
    self.url = url
    self.crashed = False
    self.sid = sid
    self.frontend_closer_func = frontend_closer_func
    self.parser_func = parser_func
    self.next_id = 1
    # stack_count must be a list
    self.stack_count = [0,]
    self.listeners = []
    self.unnotified_connect_listeners = []
    self.unnotified_event_listeners = []
    self.unnotified_cmd_response_listeners = []
    self.unnotified_event = InspectorEvent()
    self.unnotified_cmd_response_info = ResponseInfo()
    self.response_info_map = {}

  def Update(self, other):
    self.socket = other.socket
    self.url = other.url
    self.crashed = other.crashed
    self.sid = other.sid
    self.frontend_closer_func = other.frontend_closer_func
    self.parser_func = other.parser_func
    self.next_id = other.next_id
    # stack_count must be a list
    self.stack_count = other.stack_count
    self.listeners = other.listeners
    self.unnotified_connect_listeners = other.unnotified_connect_listeners
    self.unnotified_event_listeners = other.unnotified_event_listeners
    self.unnotified_cmd_response_listeners = other.unnotified_cmd_response_listeners
    self.unnotified_event = other.unnotified_event
    self.unnotified_cmd_response_info = other.unnotified_cmd_response_info
    self.response_info_map = other.response_info_map

  def _SetParserFuncForTesting(self, parser_func):
    self.parser_func = parser_func
    return

  # Overridden from DevToolsClient: 
  def GetId(self):
    return self.sid

  def WasCrashed(self):
    return self.crashed

  def ConnectIfNecessary(self):
    if self.stack_count[0]:
      return Status(kUnknownError, "cannot connect when nested")
    if self.socket.connected:
      return Status(kOk)
    self.socket.connect(self.url)
    if not self.socket.connected:
      # Try to close devtools frontend and then reconnect.
      status = self.frontend_closer_func.Run()
      if status.IsError():
        return status
      self.socket.connect(self.url)
      if not self.socket.connected:
        return Status(kDisconnected, "unable to connect to renderer")
    # shallow copy
    self.unnotified_connect_listeners = copy.copy(self.listeners)
    self.unnotified_event_listeners = []
    self.response_info_map.clear()
    #TODO (wyh)                                                            
    #    Notify all listeners of the new connection. Do this now so that any errors
    #    that occur are reported now instead of later during some unrelated call.
    #    Also gives listeners a chance to send commands before other clients.
    return self._EnsureListenersNotifiedOfConnect()
 
  def SendCommand(self, method, params):
    status = self._SendCommandInternal(method, params, {})
    return status

  def SendCommandAndGetResult(self, method, params, result):
    intermediate_result = {}
    status = self._SendCommandInternal(method, params, intermediate_result)
    if status.IsError():
      return status,
    if not intermediate_result:
      return Status(kUnknownError, "inspector response missing result")
    result.clear()
    result.update(intermediate_result)
    return status

  def AddListener(self, listener):
    self.listeners.append(listener)

  def HandleEventsUntil(self, conditional_func, timeout):
    if not self.socket.connected:
      return Status(kDisconnected, "not connected to DevTools")
    deadline = time.time() + timeout
    next_message_timeout = timeout
    while True:
      if not self.socket._recv_buffer:
        is_condition_met = False
        (status, is_condition_met) = conditional_func.Run()
        if status.IsError():
          return status
        if is_condition_met:
          return Status(kOk)
      status = self._ProcessNextMessage(-1, next_message_timeout)
      if status.IsError():
        return status
      next_message_timeout = deadline - time.time()

  def  HandleReceivedEvents(self):
    return self.HandleEventsUntil(Bind(_ConditionIsMet), 0)

  def _SendCommandInternal(self, method, params, result):
    if not self.socket.connected:
      return Status(kDisconnected, "not connected to DevTools")
    command_id = self.next_id
    self.next_id += 1
    command = {'id': command_id, 'method': method, 'params': params}
    message = json.dumps(command)
    try:
      self.socket.send(message)
    except WebSocketConnectionClosedException:
      err = "unable to send message to renderer"
      VLOG(3, err)
      return Status(kDisconnected, err)
    except:
      err = "unknown reason of socket sending failure"
      VLOG(3, err)
      return Status(kDisconnected, err)
    response_info = ResponseInfo(method)
    self.response_info_map[command_id] = response_info
    while (self.response_info_map[command_id].state) == kWaiting:
      status = self._ProcessNextMessage(command_id, 600)
      if status.IsError():
        if self.response_info_map[command_id].state == kReceived:
          del self.response_info_map[command_id]
        return status
    if self.response_info_map[command_id].state == kBlocked:
      self.response_info_map[command_id].state = kIgnored
      return Status(kUnexpectedAlertOpen)
    response = self.response_info_map[command_id].response
    if type(response.result) != dict:
      return _ParseInspectorError(response.error)
    result.clear()
    result.update(response.result)
    return Status(kOk)

  def _ProcessNextMessage(self, expected_id, timeout):
    _ScopedIncrementer(self.stack_count)
    status = self._EnsureListenersNotifiedOfConnect()
    if status.IsError():
      return status
    status = self._EnsureListenersNotifiedOfEvent()
    if status.IsError():
      return status
    status = self._EnsureListenersNotifiedOfCommandResponse()
    if status.IsError():
      return status
      # The command response may have already been received or blocked while notifying listeners. 
    if expected_id != -1 and self.response_info_map[expected_id].state != kWaiting:
      return Status(kOk)
    if self.crashed:
      return Status(kTabCrashed)
    try:
      self.socket.settimeout(timeout)
      message = self.socket.recv()
    except WebSocketConnectionClosedException:
      err = "Unable to receive message from renderer"
      VLOG(3, err)
      return Status(kDisconnected, err)
    except WebSocketTimeoutException:
      err = "Timed out receiving message from renderer: " + str(timeout)
      VLOG(3, err)
      return Status(kTimeout, err)
    except:
      err = "unknown reason of socket receiving failure"
      VLOG(3, err)
      return Status(kDisconnected, err)
    # VLOG(0, "string from recv buffer of websocket: %s" % message)
    message_type = InspectorMessageType()
    event = InspectorEvent()
    response = InspectorCommandResponse()
    self.parser_func.Update([message, expected_id, message_type, event, response])
    re = self.parser_func.Run()
    if re == False:
      VLOG(3, "Bad inspector message: " + message)
      return Status(kUnknownError, "bad inspector message: " + message)
    if message_type.typer == kEventMessageType:
      return self._ProcessEvent(event)
    return self._ProcessCommandResponse(response) 

  def _ProcessEvent(self, event):
    VLOG(0, "DEVTOOLS EVENT " + event.method + " " + str(event.params))
    self.unnotified_event_listeners = copy.copy(self.listeners)
    self.unnotified_event = event
    status = self._EnsureListenersNotifiedOfEvent()
    self.unnotified_event = InspectorEvent()
    if status.IsError():
      return status
    if event.method == "Inspector.detached":
      return Status(kDisconnected, "received Inspector.detached event")
    if event.method == "Inspector.targetCrashed":
      self.crashed = True
      return Status(kTabCrashed)
    if event.method == "Page.javascriptDialogOpening":
      #A command may have opened the dialog, which will block the response.
      #To find out which one (if any), do a round trip with a simple command
      #to the renderer and afterwards see if any of the commands still haven't
      #received a response.
      #This relies on the fact that DevTools commands are processed
      #sequentially. This may break if any of the commands are asynchronous.
      #If for some reason the round trip command fails, mark all the waiting
      #commands as blocked and return the error. This is better than risking
      #a hang.
      max_id = self.next_id
      enable_params = {"purpose": "detect if alert blocked any cmds"}
      enable_status = self.SendCommand("Inspector.enable", enable_params)
      for cur_id, response in self.response_info_map.iteritems():
	      if cur_id > max_id:
	        continue
	      if response.state == kWaiting:
	        response.state = kBlocked
      if enable_status.IsError():
	      return status
    return Status(kOk)

  def _ProcessCommandResponse(self, response):
    response_info = self.response_info_map.get(response.sid, None)
    if None == response_info:
      return Status(kUnknownError, "unexpected command response")
    else:
      method = response_info.method
      if response.result:
        result = str(response.result)
      else:
        result = response.error
      VLOG(0, "DEVTOOLS RESPONSE " +  method + " (id= " + str(response.sid) + ") " + result)
      if response_info.state == kReceived:
        return Status(kUnknownError, "received multiple command responses")
      if response_info.state == kIgnored:
        del self.response_info_map[response.sid]
      else:
        response_info.state = kReceived
        response_info.response.sid = response.sid
        response_info.response.error = response.error
        if response.result:
          response_info.response.result = response.result

      if type(response.result) == dict:
        self.unnotified_cmd_response_listeners = copy.copy(self.listeners)
        self.unnotified_cmd_response_info = response_info
        status = self._EnsureListenersNotifiedOfCommandResponse()
        self.unnotified_cmd_response_info = ResponseInfo()
        if status.IsError():
          return status
      return Status(kOk)
  
  def _EnsureListenersNotifiedOfConnect(self):
    while len(self.unnotified_connect_listeners):
      listener = self.unnotified_connect_listeners[0]
      del self.unnotified_connect_listeners[0]
      status = listener.OnConnected(self)
      if status.IsError():
        return status
    return Status(kOk)
  
  def _EnsureListenersNotifiedOfEvent(self):
    while len(self.unnotified_event_listeners):
      listener = self.unnotified_event_listeners[0]
      del self.unnotified_event_listeners[0]
      status = listener.OnEvent(self, self.unnotified_event.method, self.unnotified_event.params)
      if status.IsError():
        return status
    return Status(kOk)

  def _EnsureListenersNotifiedOfCommandResponse(self):
    while len(self.unnotified_cmd_response_listeners):
      listener = self.unnotified_cmd_response_listeners[0]
      del self.unnotified_cmd_response_listeners[0]
      status = listener.OnCommandSuccess(self, self.unnotified_cmd_response_info.method)
      if status.IsError():
        return status
    return Status(kOk)

