from webob import exc

from util.f import always
from pymonad_extra.util.either import fold
from pymonad_extra.util.task import reject

def dispatch(parser, router):
  # (Request -> Either Exception Route) -> (Request -> (Route -> Task Exception Dict)) -> Task Exception Dict

  def _dispatch(req):
    return fold(
      always( reject(exc.HTTPNotFound()) ),
      router(req),
      parser(req)
    )

  return _dispatch

