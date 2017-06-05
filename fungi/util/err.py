"""
A stupid wrapper around python exceptions to capture the stack trace.
Use within exception-handlers of Task functions like this:
    
    except SomeError as e:
      rej(err.wrap(e))

"""
import sys
import traceback

from pymonad_extra.Task import Task
from pymonad.Either import Left, Right

def wrap(e):
  return Err(e,sys.exc_info())

class Err(object):
  def __init__(self,e,exc):
    self.error = e
    self.exc = exc

  def __str__(self):
    trace = traceback.format_exception(*self.exc)
    if len(trace) <= 1:
      return unicode(self.error)
    else:
      dump = u"".join(trace)
      return u"%s\n%s" % (unicode(self.error),dump)

      
# decorators

def left_errors(fn):
  # (*a, **b -> c) -> Either Err c

  def _wrap(*a,**kw):
    try:
      return Right( fn(*a,**kw) )
    except Exception as e:
      return Left( wrap(e) )
  _wrap.__name__ = fn.__name__
  return _wrap


def reject_errors(fn):
  # (*a, **b -> c) -> Task Err c

  def _wrap(*a,**kw):
    def _task(rej,res):
      try:
        res( fn(*a,**kw) )
      except Exception as e:
        rej( wrap(e) )
    return Task(_task)
  _wrap.__name__ = fn.__name__
  return _wrap

def reject_errors_task(fn):
  # (*a, **b -> Task x c) -> Task Err c

  def _wrap(*a,**kw):
    try:
      return fn(*a,**kw)
    except Exception as e:
      return reject( wrap(e) )
  _wrap.__name__ = fn.__name__
  return _wrap


