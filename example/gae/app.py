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

from typing import Union, NamedTuple
from util.f import identity, always
from pymonad_extra.util.task import resolve
from pymonad_extra.util.maybe import with_default
from util.union import match

from fungi.core import dispatch
from fungi.parse import parse_route, one_of, all_of, s, format, method, number
from fungi.gae.memcache import cache_get
from fungi.gae.user import current as current_user, login_url
from fungi.wsgi import adapter, from_html, redirect_to

redirect_to_login = lambda url: login_url(url).fmap( redirect_to ) 

HomeR = NamedTuple('HomeR',[])
Routes = Union[HomeR]    

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

def route(req):
  return (
    match(Routes, {
      HomeR: always(render_home(req))
    })
  )

def render_home(req):
  def _get_nick(u):
    return cache_get( "/".join(('session',u.email(),'nick')), resolve(u.nickname()) )

  def _render(nick):
    return "<h1><a href=\"%s\">Hello, %s!</a></h1>" % ( encode_path(HomeR()), nick )
  
  return (
    with_default(
      redirect_to_login(req.url), 
      current_user().fmap( 
        lambda u: _get_nick(u).fmap(_render).fmap(from_html) 
      )
    )
  )

main = adapter(log, dispatch(parse_route(route_parser), route))


