import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

from typing import Union, NamedTuple
from f import always, identity, always
from pymonad.Either import Left, Right
from pymonad.Maybe import Just, Nothing
from eitherutil import fold
from taskutil import resolve
from unionutil import match

from core import dispatch
from reqparse import parse, one_of, all_of, s, format, method

from wsgi import adapter

HomeR = NamedTuple('HomeR',[])
NullR = NamedTuple('NullR',[]) 
Routes = Union[HomeR,NullR]    # Note Union types stupidly flatten unless >1 types

encode_path = (
  match(Routes, {
    HomeR: always("/"),
    type(None): (lambda : "")
  })
)

def parse_route(req):
  return parse( identity, route_parser, req ) 

route_parser = (
  one_of([
    format( HomeR, all_of([ method("GET"), s("") ]) )
  ])
)

def route(req):
  return (
    match(Routes, {
      HomeR:      always(render_home(req)),
      type(None): (lambda: resolve({}))
    })
  )

def render_home(req):
  return resolve({"body": "<h1><a href=\"%s\">Hello world!</a></h1>" % encode_path(HomeR()) })

main = adapter(log, dispatch(parse_route, route))

if __name__ == '__main__':
  
  from wsgiref.simple_server import make_server

  httpd = make_server('', 8080, main)
  httpd.serve_forever()

