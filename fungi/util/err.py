"""
A stupid wrapper around python exceptions to capture the stack trace.
Use within exception-handlers of Task functions like this:
    
    except SomeError as e:
      rej(err.wrap(e))

"""

import sys
import traceback

def wrap(e):
  return Err(e,sys.exc_info()[2])

class Err(object):
  def __init__(self,e,tb):
    self.error = e
    self.traceback = tb

  def __str__(self):
    return "%s\n%s" % (str(self.error), traceback.format_exc(self.traceback))


