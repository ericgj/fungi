from google.appengine.api import users

from pymonad_extra.Task import Task
import fungi.util.err as err

def current():
  def _current(rej,res):
    try:
      res( users.get_current_user() )
    except Exception as e:
      rej( err.wrap(e) )
  return Task(_current)


