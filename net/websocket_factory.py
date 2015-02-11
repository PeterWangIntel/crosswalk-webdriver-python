import socket
from third_party.websocket_client.websocket import create_connection as _create_connection
from third_party.websocket_client.websocket import WebSocketException
from third_party.websocket_client.websocket import WebSocketTimeoutException
from base.log import VLOG

class WebsocketFactory(object):

  def create_connection(self, url="", timeout=None, **kwargs):
    #VLOG(0, "trigger WebsocketFactory' create_connection")
    sockopt = kwargs.get('sockopt', [])
    sockopt.append((socket.SOL_SOCKET, socket.SO_REUSEADDR, 1))
    kwargs['sockopt'] = sockopt
    # we temporary move out **kwargs option(ignore)
    # and let websocket be quiet after initialization
    return _create_connection(url, timeout, **kwargs)

