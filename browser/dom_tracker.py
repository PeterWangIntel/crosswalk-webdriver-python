__all__ = ["DomTracker"]

from devtools_event_listener import DevToolsEventListener
from status import *
import json

# Tracks the state of the DOM and execution context creation.
class DomTracker(DevToolsEventListener):

  def __init__(self, client):
    DevToolsEventListener.__init__(self)
    self.node_to_frame_map = {}
    client.AddListener(self)

  # return status and frame_id<string>
  def GetFrameIdForNode(self, node_id):
    frame_id = self.node_to_frame_map.get(node_id, None)
    if frame_id == None:
      return (Status(kNoSuchFrame, "element is not frame"), "")
    return (Status(kOk), frame_id)

  # Overridden from DevToolsEventListener:
  def OnEvent(self, client, method, params):
    if method == "DOM.setChildNodes":
      nodes = params.get("nodes")
      if nodes == None:
        return Status(kUnknownError, "DOM.setChildNodes missing 'nodes'")
      if not self._ProcessNodeList(nodes):
        js = json.dumps(nodes)
        return Status(kUnknownError, "DOM.setChildNodes has invalid 'nodes': " + js)
    elif method == "DOM.childNodeInserted":
      node = params.get("node")
      if node == None:
        return Status(kUnknownError, "DOM.childNodeInserted missing 'node'")
      if not self._ProcessNode(node):
        js = json.dumps(node)
        return Status(kUnknownError, "DOM.childNodeInserted has invalid 'node': " + js)
    elif method == "DOM.documentUpdated":
      self.node_to_frame_map.clear()
      params = {}
      client.SendCommand("DOM.getDocument", params)
    return Status(kOk)

  def OnConnected(self, client):
    self.node_to_frame_map.clear()
    # Fetch the root document node so that Inspector will push DOM node
    # information to the client.
    params = {}
    return client.SendCommand("DOM.getDocument", params)

  def _ProcessNodeList(self, nodes_list=[]):
    if type(nodes_list) != list:
      return False
    for node in nodes_list:
      #if not node:
      #  return False
      if not self._ProcessNode(node):
        return False
    return True

  def _ProcessNode(self, node):
    dic = node
    if type(dic) != dict:
      return False
    node_id = dic.get("nodeId")
    if type(node_id) != int:
      return False
    frame_id = dic.get("frameId")
    if type(frame_id) == str:
      self.node_to_frame_map[node_id] = frame_id
    children = dic.get("children")
    if children:
      return self._ProcessNodeList(children)
    return True

