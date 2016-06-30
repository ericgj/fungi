from wsgi import adapter
from core import dispatch
from parse import parse_route

class InitError(Exception):
  pass

def mount(parser, router, config=(), init=None):
  def _raise(e):
    raise InitError(unicode(e))

  def _set_config(c):
    hook['config'] = c

  if init is None:
    return adapter(dispatch(parse_route(parser), router, config))
  else:
    hook = { 'config': () }
    init.fork(_raise, _set_config)
    return mount(parser, router, config=hook['config'])

