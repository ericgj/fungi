from google.appengine.api import users

from pymonad.Maybe import Just, Nothing
from pymonad_extra.Task import Task
import fungi.util.err as err

def current():
  try:
    return Just(users.User())  # throws AssertionError / UserNotFoundError
  except Exception as e:
    return Nothing


def login_url(dest_url):
  def _login_url(rej,res):
    try:
      res( users.create_login_url(dest_url=dest_url) )
    except Exception as e:
      rej( err.wrap(e) )
  return Task(_login_url)

