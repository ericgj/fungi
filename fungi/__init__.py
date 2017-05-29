from webob import exc
from wsgi import adapter
from parse import parse_route

from util.f import always, curry, debug
import pymonad_extra.util.either as either
import pymonad_extra.util.task as task


def mount(parser, router):
  return adapter( dispatch( parse_route(parser), router ) )

def mount_with_config(parser, router, config):
  return adapter( dispatch_with_config( parse_route(parser), router, config ) )

def mount_with_init(parser, router, init):
  return (
    ( init >> dispatch_with_config( parse_route(parser), router ) )
      .fmap(adapter)
  )

def dispatch(parser, router):
  # (Request -> Either Exception Route) 
  #  -> (Request -> (Route -> Task Exception Dict)) 
  #  -> Task Exception Dict

  def _dispatch(req):
    return either.fold(
      always( task.reject(exc.HTTPNotFound()) ),
      router(req),
      parser(req)
    )

  return _dispatch


@curry
def dispatch_with_config(parser, router, config):
  # (Request -> Either Exception Route) 
  #  -> (config -> Request -> (Route -> Task Exception Dict)) 
  #  -> config
  #  -> Task Exception Dict

  def _dispatch(req):
    return either.fold(
      always( task.reject(exc.HTTPNotFound()) ),
      router(config, req),
      parser(req)
    )

  return _dispatch

