
"""  
# TODO types -- waiting for Monad typedefs
from typing import Callable, List, NamedTuple, Tuple, TypeVar, Iterable

# type aliases
T = TypeVar("T")
Handler =  Callable[[List[unicode],Request], Task[Exception,Response]] 
Decoder = Callable[[Request], Maybe[List[unicode]]]
Encoder = Callable[[List[unicode]], Result[Exception,unicode]]

# data types
Route = (
  NamedTuple('Route', [
    ('name', unicode),
    ('decoder', Decoder),
    ('encoder', Encoder),
    ('handler', Handler)
  ])
)
"""

from collections import namedtuple
from webob import exc

from pymonad.Either import Left
from maybeutil import with_default
from taskutil import resolve

Route = namedtuple('Route', ['name','decoder','encoder','handler'])

class RouteEncodingNotFound(Exception):
  def __init__(self,name):
    super(Exception,self).__init__(
      "Unable to encode route named '%s': not found" % name)
    )
    self.name = name


def router(routes):
  # type: List[Route] -> Callable[[Request], Task[Exception,Response]]
  
  def _route(req):
    # type: Request -> Task[Exception,Response]

    m = first_of( decode(r, req) for r in routes )
    return with_default(
      resolve( exc.HTTPNotFound() ),
      m.fmap( fapply(route) )
    )
  return _route


# Note: "uri_for" helper
def encoder(routes):
  # type: Router -> Callable[[List[unicode]], Result[Exception,unicode]]

  def _encode(args=[]):
    # type: List[str] -> Result[Exception,str]

    try:
      return next( encode(r, args) for r in routes if r.name == name )
    except StopIteration:
      return Left(RouteEncodingNotFound(name))
  return _encode


def decode(r, req):
  # type: Route -> Request -> Maybe[Tuple[Handler,List[unicode],Request]] 
  
  return r.decoder(req).fmap(lambda args: (r.handler,args,req))


def encode(r, args):
  # type: Route -> List[unicode] -> Result[Exception,unicode]
  
  return r.encoder(args)


def route(handler, args, req):
  # type: Handler -> List[str] -> Request -> Task[Exception,Response]
  
  return handler(args,req)



def first_of(iter):
  # type: Iterable[Maybe[T]] -> Maybe[T]

  for m in iter:
    if isinstance(m,Just):
      return m
  return Nothing

