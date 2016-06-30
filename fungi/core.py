from webob import exc

from util.f import always
from pymonad_extra.util.either import fold
from pymonad_extra.util.task import reject

def dispatch(parser, router, config):
  # (Request -> Either Exception Route) 
  #  -> (Request -> (Route -> Task Exception Dict)) 
  #  -> Dict 
  #  -> Task Exception Dict

  def _dispatch(req):
    return fold(
      always( reject(exc.HTTPNotFound()) ),
      router(req,config),
      parser(req)
    )

  return _dispatch

