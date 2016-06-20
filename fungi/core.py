from webob import exc
from f import always
from eitherutil import fold
from taskutil import reject

def dispatch(parser, router):
  # (Request -> Either Exception Route) -> (Request -> (Route -> Task Exception Dict)) -> Task Exception Dict
  # type: Callable([Request],Either[Exception,Route]) -> Callable([Request],Callable([Route],Task[Exception,Dict])) -> Task[Exception,Dict]

  def _dispatch(req):
    return fold(
      always( reject(exc.HTTPNotFound()) ),
      router(req),
      parser(req)
    )

  return _dispatch

