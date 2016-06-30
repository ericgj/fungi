import os.path
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

from typing import Union, NamedTuple
from fungi.util.f import identity, always
from pymonad.Either import Left, Right
from pymonad_extra.util.either import fold, with_default
from pymonad_extra.Task import Task
from pymonad_extra.util.task import resolve, reject
from fungi.util.union import match

from fungi import mount
from fungi.parse import one_of, all_of, s, format, method, number
from fungi.wsgi import adapter, encode_json, from_html
import fungi.util.json_ as json_
import fungi.util.err as err

HomeR = NamedTuple('HomeR',[])
Routes = Union[HomeR]    

def local_file(fname):
  return os.path.join(os.path.dirname(__file__), fname)

encode_path = (
  match(Routes, {
    HomeR: always("/")
  })
)

route_parser = (
  one_of([
    format( HomeR, all_of([ method("GET"), s("") ]) )
  ])
)

def route(req,config):
  return (
    match(Routes, {
      HomeR: always(render_home(req, config))
    })
  )

def render_home(req,config):
  secret = (
           Right(config['secret']) if config.has_key('secret') 
      else Left(KeyError('No secret found in config')) 
  )

  contents = (
    secret.fmap( lambda s: (
      "<h1><a href=\"%s\">Your secret is: %s!</a></h1>" % (encode_path(HomeR()), s)
    ))
  )

  return (
    fold(
      reject,
      lambda c: resolve(c).fmap(from_html),
      contents
    )
  )


def load_secret(rej,res):
  try:
    with open(local_file('secret.json')) as f:
      res( with_default({}, json_.decode(f.read())) )
  except Exception as e:
    rej( err.wrap(e) )

main = mount(route_parser, route, init=Task(load_secret))

if __name__ == '__main__':
  
  from wsgiref.simple_server import make_server

  httpd = make_server('', 8080, main)
  httpd.serve_forever()

