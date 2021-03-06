from google.appengine.api import users

from pymonad.Maybe import Just, Nothing
from pymonad_extra.util.maybe import with_default
from pymonad.Either import Left, Right
from pymonad_extra.util.either import fold
from pymonad_extra.Task import Task
from pymonad_extra.util.task import reject, resolve
import fungi.util.err as err
from fungi.wsgi import redirect_response

def current():
  # () -> Maybe User
  try:
    u = users.get_current_user()
    if u is None:
      return Nothing
    else:
      return Just(u)
  except Exception as e:
    return Nothing


def login_url(dest_url):
  # String -> Either Exception String
  try:
    return Right( users.create_login_url(dest_url=dest_url) )
  except Exception as e:
    return Left( err.wrap(e) )


def current_or_redirect_to_login(dest_url):
  # String -> Task (HTTPRedirection | Exception) User

  muser = current()
  return with_default(
    fold(reject, reject, login_url(dest_url).fmap(redirect_response)),
    muser.fmap(resolve)
  )


