from google.appengine.api import users

from pymonad.Maybe import Just, Nothing
from pymonad_extra.util.maybe import with_default
from pymonad_extra.Task import Task
from pymonad_extra.util.task import reject, resolve
import fungi.util.err as err
from fungi.wsgi import redirect_response

def current():
  try:
    u = users.get_current_user()
    if u is None:
      return Nothing
    else:
      return Just(u)
  except Exception as e:
    return Nothing


def login_url(dest_url):
  def _login_url(rej,res):
    try:
      res( users.create_login_url(dest_url=dest_url) )
    except Exception as e:
      rej( err.wrap(e) )
  return Task(_login_url)


def current_or_redirect_to_login(dest_url):
  # String -> Task HTTPRedirection User

  muser = current()
  return with_default(
    (login_url(dest_url).fmap(redirect_response)) >> reject,
    muser.fmap(resolve)
  )


