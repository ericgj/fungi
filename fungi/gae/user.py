from google.appengine.api import users

from pymonad.Maybe import Just, Nothing
from pymonad_extra.util.maybe import with_default
from pymonad.Either import Left, Right
from pymonad_extra.util.either import fold
from pymonad_extra.util.task import reject, resolve
from fungi.util.err import left_errors
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


@left_errors
def login_url(dest_url):
  # String -> Either Exception String
  return users.create_login_url(dest_url=dest_url)


def current_or_redirect_to_login(dest_url):
  # String -> Task (HTTPRedirection | Exception) User

  muser = current()
  return with_default(
    fold(reject, reject, login_url(dest_url).fmap(redirect_response)),
    muser.fmap(resolve)
  )


