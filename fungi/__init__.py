from wsgi import adapter
from core import dispatch
from parse import parse_route

def mount(log, parser, router):
  return adapter(log, dispatch(parse_route(parser), router))

