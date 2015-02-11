import optparse
import os
import sys
import time
import threading
import BaseHTTPServer
from server.http_handler import XwalkHttpHandlerWrapper
from net.port_server import PortServer
from base.log import InitLogging
from base.log import VLOG
from base.bind import Bind

def main(argv):
  ''' main entrance of xwalkdriver '''
  # default setting for CrossWalk WebDriver
  port = "9515"
  host_name = ""
  port_server = None
  target = "android"

  # Parse command line flag.
  parser = optparse.OptionParser()
  parser.add_option('--port', action='store', dest="port", type='int', help='port to listen on')
  parser.add_option('--target', action='store', dest="target", type='str', help='target device, e.g --target=android')
  parser.add_option('--log-path', action='store', dest="log_path", help='write server log to file instead of stderr, increase log level to INFO')
  parser.add_option('--verbose', action='store_false', dest="verbose", help='log verbosely')
  parser.add_option('--silent', action='store_false', dest="silent", help='log nothing')
  parser.add_option('--url-base', action='store', dest="url_base", help='base URL path prefix for command, e.g. wd/url')
  parser.add_option('--port-server', action='store', dest="port_server", help='address of server to contact for reserving a port')

  # info user HOWTO:
  if 1 == len(argv):
    parser.print_help()
  
  # choose specific port to listen on
  (opts, _) = parser.parse_args()
  if opts.port:
    port = opts.port

  # choose specific port server to maintain port for devtools
  if opts.port_server:
    if 'linux2' != sys.platform:
      print "Warning: port-server not implemented for this platform."
      sys.exit(-1)
    else:
      if not opts.port_server.startswith('@'):
        print "Invalid port-server. Exiting..."
        sys.exit(-1)
      else:
        path = "\0"
        path += opts.port_server[1:]
        port_server = PortServer(path)

  if opts.url_base == None:
    url_base = ""
  else:
    url_base = str(opts.url_base)
  if not url_base or not url_base.startswith('/'):
    url_base = "/" + url_base
  elif url_base[-1] != '/':
    url_base = url_base + '/'

  # choose specific device for testing
  if opts.target:
    target = opts.target.lower()
    Handler = XwalkHttpHandlerWrapper(port, url_base, target, port_server)
  else:
    Handler = XwalkHttpHandlerWrapper(port, url_base, target, port_server)
  
  if not opts.silent:
    print "Starting XwalkDriver on port %s" % port

  if False == InitLogging(opts):
    print "Unable to initialize logging. Exiting..."
    sys.exit(-1)
  
  VLOG(0, "Running on target device " + target)

  # Running Http Server
  httpd = BaseHTTPServer.HTTPServer((host_name, int(port)), Handler)
  VLOG(1, "Xwalk Http Server Starts - %s:%s" % (host_name, port))
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    VLOG(1, "Xwalk Http Server Stops - %s:%s" % (host_name, port))
    httpd.server_close()
  finally:
    # scan and make the directory tree clean every time 
    for rootdir, subdir, files in os.walk("./"):
      for item in files:
        if item.endswith(".pyc"):
          try:
            os.remove(rootdir + "/" + item)
          except:
            pass

    # retrieve zombie thread in case of Ctrl-C crosswalk webdriver ohther than call dirver.quit() in selenium side
    for zombie in threading.enumerate():
      if zombie != threading.current_thread():
        quit_thread_cmd = Bind(Bind._RunNothing)
        quit_thread_cmd.is_quit_func_ = True
        zombie.PostTask(quit_thread_cmd)

  sys.exit(0) # end of main

if __name__ == '__main__':
  main(sys.argv)

