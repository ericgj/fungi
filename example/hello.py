import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

from typing import Union, NamedTuple
from fungi.util.f import identity, always
from pymonad_extra.util.task import resolve
from fungi.util.union import match

from fungi import mount
from fungi.parse import one_of, all_of, s, format, method, number
from fungi.wsgi import adapter, encode_json, from_html

HomeR = NamedTuple('HomeR',[])
JsonR = NamedTuple('JsonR',[('id',int)])
Routes = Union[HomeR,JsonR]    

encode_path = (
  match(Routes, {
    HomeR: always("/"),
    JsonR: lambda id: "/item/%d" % id
  })
)

route_parser = (
  one_of([
    format( HomeR, all_of([ method("GET"), s("") ]) ),
    format( JsonR, all_of([ method("GET"), s("item"), number ]) ) 
  ])
)

def route(req,_):
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
  return resolve({ "id": id }) >> encode_json


main = mount(log, route_parser, route)

if __name__ == '__main__':
  
  from wsgiref.simple_server import make_server

  httpd = make_server('', 8080, main)
  httpd.serve_forever()

