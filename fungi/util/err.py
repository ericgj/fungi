"""
A stupid wrapper around python exceptions to capture the stack trace.
Use within exception-handlers of Task functions like this:
    
    except SomeError as e:
      rej(err.wrap(e))

"""
import sys
import traceback

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

