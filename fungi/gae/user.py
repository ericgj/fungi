from google.appengine.api import users

from fungi.taskmonad import Task
import fungi.err as err

def current():
  def _current(rej,res):
    try:
      res( users.get_current_user() )
    except Exception as e:
      rej( err.wrap(e) )
  return Task(_current)


