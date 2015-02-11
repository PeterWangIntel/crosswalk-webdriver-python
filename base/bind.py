__all__ = ["Bind"]

from log import VLOG
from browser.status import *

""" Bind class accept 2 parameters: a callable function and a list where variable 
parameters packed in.

there're 2 ways binding: you can use "Bind(func, [argument0, argument1, ...])"
as an early binding, also you can use "Bind(func)" as a dynamical binding. when truly 
run it you need call Update([argument0, argument1, ...]) at first.

FYI, the execute function should not be uncallable ones, when casually init an uncallable
execute function willl result in exception """

class Bind(object):

  # default execute funtion doing nothing
  @staticmethod
  def _RunNothing():
    return Status(kOk)

  def __init__(self, runner=None, args=[]):
    if callable(runner) == False:
      VLOG(0, "execute function isn't callable")
      raise Exception("execute function isn't callable")
    try:
      self.runner = runner
      self.args = args
    except:
      self.runner = Bind._RunNothing
 
  def Update(self, args=[]):
    self.args = args
  
  def Run(self):
    return self.runner(*(self.args))

