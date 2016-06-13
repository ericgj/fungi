from structlog import get_logger
log = get_logger(__name__)

from pymonad.Either import Left, Right
from pymonad.Maybe import Just, Nothing
from taskutil import resolve

from core import Route, router, encoder
from wsgi import adapter

def decode_home(req):
  if req.path == '/':
    return Just([])
  else
    return Nothing

def encode_home(args):
  if len(args)==0:
    return Right('/')
  else:
    return Left(Exception('Unable to encode: too many args'))

def render_home(req,args):
  return resolve({"body": "<h1><a href=\"%s\">Hello world!</a></h1>" % uri_for('home') })

routes = [
  Route( 'home', decode_home, encode_home, render_home )
]

uri_for = encoder(routes)
app = router(routes)
main = adapter(log, app)

