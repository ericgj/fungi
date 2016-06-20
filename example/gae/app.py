"""
An example GAE app making use of memcache for session data
"""

import os.path
def local_file(fname):
  return os.path.join(os.path.dirname(__file__),fname)

from google.appengine.ext import vendor
vendor.add(local_file('lib'))

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

from json import JSONEncoder
from typing import Union, NamedTuple
from util.f import identity, always
from pymonad_extra.util.task import resolve
from util.union import match

from fungi.core import dispatch
from fungi.reqparse import parse, one_of, all_of, s, format, method, number
from fungi.gae.memcache import cache_get
from fungi.gae.user import current as current_user
from fungi.wsgi import adapter, encode_json, from_html


HomeR = NamedTuple('HomeR',[])
Routes = Union[HomeR]    

encode_path = (
  match(Routes, {
    HomeR: always("/")
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
      HomeR: always(render_home(req).fmap(from_html))
    })
  )

def render_home(req):
  def _get_nick(u):
    return cache_get( "/".join(('session',u.email(),'nick')), resolve(u.nickname()) )

  def _render(nick):
    return "<h1><a href=\"%s\">Hello, %s!</a></h1>" % ( encode_path(HomeR()), nick )
  
  return (
    (current_user() >> _get_nick).fmap(_render)
  )

main = adapter(log, dispatch(parse_route, route))


