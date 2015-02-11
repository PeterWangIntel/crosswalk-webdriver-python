__all__ = ["InitLogging", \
           "VLOG", \
           "DEBUG", \
           "INFO", \
           "WARNING", \
           "ERROR", \
           "CRITICAL"]

import time
import sys
import logging
import copy

DEFAULT_LOGGER_NAME = "\033[1;42m" + "Log" + "\033[1;0m"
DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3
CRITICAL = 4

""" InitLogging should only be invoked on main thread, aka before the http handler, 
and we only use one true logger whose name is set by "DEFAULT_LOGGER_NAME", wherever
need a log you just call VLOG(), the only logger is global scoped """
def InitLogging(opts):
  logging.addLevelName(logging.DEBUG, "\033[1;44m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
  logging.addLevelName(logging.INFO, "\033[1;45m%s\033[1;0m" % logging.getLevelName(logging.INFO))
  logging.addLevelName(logging.WARNING, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
  logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
  logging.addLevelName(logging.CRITICAL, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))

  g_level = logging.DEBUG

  if '--verbose' in sys.argv:
    g_level = logging.DEBUG

  if '--silent' in sys.argv:
    g_level = logging.NOTSET

  logger = logging.getLogger(DEFAULT_LOGGER_NAME)
  logger.setLevel(g_level)
  g_start_time = time.asctime()
  g_formatter = logging.Formatter('\033[1;33m%(asctime)s\033[1;0m %(name)s %(levelname)s %(message)s')

  if opts.log_path:
    try:
      log_file = open(opts.log_path, "w")
    except:
      print "Failed to redirect stderr to log file"
      return False
    sys.stderr = log_file
    # create a handler to write the log to a given file
    fh = logging.FileHandler(log_path)
    fh.setLevel(g_level)
    fh.setFormatter(g_formatter)
    logger.addHandler(fh)

  # we direct the log information to stdout 
  ch = logging.StreamHandler(sys.__stdout__)
  ch.setLevel(g_level)
  ch.setFormatter(g_formatter)
  logger.addHandler(ch)
  return True

# dispatch difference level to logger created by InitLogging()
def VLOG(level, msg):
  logger = logging.getLogger(DEFAULT_LOGGER_NAME)
  if level == DEBUG:
    logger.debug('\033[1;34m' + msg + '\033[1;0m')
  elif level == INFO:
    logger.info('\033[1;35m' + msg + '\033[1;0m')
  elif level == WARNING: 
    logger.warning('\033[1;31m' + msg + '\033[1;0m')
  elif level == ERROR: 
    logger.error('\033[1;31m' + msg + '\033[1;0m')
  elif level == CRITICAL: 
    logger.critical('\033[1;31m' + msg + '\033[1;0m')
  else:
    logger.debug('\033[1;34m' + msg + '\033[1;0m')
  return

