import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

from json import JSONEncoder
from typing import Union, NamedTuple
from f import identity, always
from taskutil import resolve
from unionutil import match

from core import dispatch
from reqparse import parse, one_of, all_of, s, format, method, number

from wsgi import adapter, encode_json, from_html

HomeR = NamedTuple('HomeR',[])
JsonR = NamedTuple('JsonR',[('id',int)])
Routes = Union[HomeR,JsonR]    

encode_path = (
  match(Routes, {
    HomeR: always("/"),
    JsonR: lambda id: "/item/%d" % id
  })
)

def parse_route(req):
  return parse( identity, route_parser, req ) 

route_parser = (
  one_of([
    format( HomeR, all_of([ method("GET"), s("") ]) ),
    format( JsonR, all_of([ method("GET"), s("item"), number ]) ) 
  ])
)

def route(req):
  return (
    match(Routes, {
      HomeR: always(render_home(req)),
      JsonR: render_item
    })
  )

def render_home(req):
  return (
    resolve(
      "<h1><a href=\"%s\">Hello world!</a></h1>" % encode_path(HomeR())
    ).fmap(from_html)
  )

def render_item(id):
  return resolve({ "id": id }) >> encode_json(JSONEncoder)


main = adapter(log, dispatch(parse_route, route))

if __name__ == '__main__':
  
  from wsgiref.simple_server import make_server

  httpd = make_server('', 8080, main)
  httpd.serve_forever()

