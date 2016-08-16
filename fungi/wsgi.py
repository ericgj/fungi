import logging
from json import JSONEncoder
from webob import Request, Response, exc

from pymonad_extra.Task import Task
from pymonad_extra.util.either import to_task, with_default
from util.f import curry, merge, assoc, dissoc, identity
from util.json_ import pretty_encode, encode_with
import util.err

log = logging.getLogger(__name__)
def debug_log(msg,x):
  log.debug("%s : %s" % (msg,x))
  return x

# --- Response helpers

@curry
def from_string(spec,s):
  # (String, String) -> (String | (String,Cookies)) -> (Dict | (Dict,Cookies)) 
 
  ctype, charset = spec
  def _attrs(t):
    status = 200
    return {
      'status': status, 'content_type': ctype, 'charset': charset,
      'body': unicode(t)     # webob handles encoding
    }
  
  return _if_tuple(
    lambda t,c: (_attrs(t),c), 
    lambda t:    _attrs(t),
    s
  )

from_html = from_string(('text/html','utf8'))
from_text = from_string(('text/plain', 'utf8'))

@curry
def encode_json_with(encoder,data):
  # JSONEncoder -> (Dict | (Dict,Cookies)) -> Task Exception (Dict | (Dict,Cookies))

  from_json_s = from_string(('application/json','utf8'))
  return _if_tuple(
    lambda d,c: (
      to_task(encode_with(encoder,d))
        .fmap(lambda s: (from_json_s( debug_log("encode_json_with",s) ),c))
    ),
    lambda d:   (
      to_task(encode_with(encoder,d))
        .fmap(lambda s: from_json_s( debug_log("encode_json_with",s) ))
    ),
    data
  )

encode_json = encode_json_with(JSONEncoder)

@curry
def template(spec,tmpl,data):
  # (String, String) -> {render: Dict -> String} -> (Dict | (Dict,Cookies)) -> Task Exception (Dict | (Dict,Cookies))
  
  ctype, charset = spec
  from_s = from_string((ctype,charset))
  return _if_tuple(
    lambda d,c: render(tmpl,d).fmap(lambda s: (from_s(s), c)),
    lambda d:   render(tmpl,d).fmap(from_s),
    data
  )

template_html = template(('text/html','utf-8'))
template_text = template(('text/plain','utf-8'))

@curry
def add_headers(hdrlist,attrs):
  # List (String, String) -> (Dict | (Dict,Cookies)) -> (Dict | (Dict,Cookies))

  def _appendhdrs(at):
    return assoc('headerlist', at.get('headerlist',[]) + hdrlist, at)

  return _if_tuple(
    lambda at,c: (_appendhdrs(at), c),
    lambda at:    _appendhdrs(at)    ,
    attrs
  )
    
def redirect_to(url):
  # String -> (Dict | (Dict,Cookies))
  return add_headers([('Location',url)], {'status': 303}) 


def redirect_response(url):
  return exc.HTTPSeeOther(location=url)

# --- WSGI app adapter

def adapter(func):
  # (Request -> Task Exception Dict) -> WSGIApp
  
  def _adapter(environ, start_response):
    def _attach(resp):
      req.response = resp

    req = Request(environ)
    req.response = exc.HTTPNotImplemented()

    task = func(req).bimap(
      build_error_response,
      build_success_response
    )
    task.fork(_attach, _attach)

    return req.response(environ, start_response)

  return _adapter

@curry
def adapter_with_cookies(writer,func):
  # (Cookies -> Response -> Task Exception Response) 
  # -> (Request -> Task Exception (Dict,Cookies)) 
  # -> WSGIApp
  
  def _adapter(environ, start_response):
    def _build_and_save_cookies((attrs,cs)):
      resp = build_success_response(attrs)
      if isinstance(resp, Response):                  # a kludge
        return writer(cs, resp).fmap(always(resp))
      else:
        return resolve(resp)

    def _attach(resp):
      req.response = resp

    req = Request(environ)
    req.response = exc.HTTPNotImplemented()

    task = (
      ( func(req) >> _build_and_save_cookies ).bimap(
          build_error_response,
          identity
        )
    )
    task.fork(_attach, _attach)

    return req.response(environ, start_response)

  return _adapter


def build_error_response(e):
  # Exception -> HTTPError

  try:
    log.error('build_error_response: %s', unicode(e), extra={'error': e} )
    if isinstance(e,exc.HTTPError) or isinstance(e,exc.HTTPRedirection):
      return e
    else:
      tmpl = '${explanation}<br/><br/><pre>${detail}</pre>${html_comment}'
      return exc.HTTPInternalServerError(detail=str(e), body_template=tmpl)   # Note: assumes ASCII repr
      
  except Exception as e_:
    return exc.HTTPInternalServerError(detail="Error in building error response", comment=str(e_))

def build_success_response(attrs):
  # Dict -> WSGIApp

  try:
    attrs = merge({'status': 200}, attrs)
    attrs_ = dissoc('body',attrs)
    log.debug('build_success_response: (body omitted)\n%s' % with_default({}, pretty_encode(attrs_)), 
              extra={'response': attrs_}) 
    resp = Response(**attrs)
    log.info('build_success_response: %s' % attrs.get('status'),  
             extra={'status': attrs.get('status')})     # TODO a little more info
    return resp

  # TODO: include backtrace
  except Exception as e:
    return build_error_response( 
      exc.HTTPInternalServerError(detail="Error in building response", comment=str(e))
    )

# --- utils

# Note: as standalone function, Either would make more sense. But easier
# to deal with as a Task here.

def render(tmpl,data):
  def _render(rej,res): 
    try:
      res( tmpl.render(data) )

    except Exception as e:
      rej(err.wrap(e))

  return Task(_render)



def _if_tuple(iftrue,iffalse,x):
  if isinstance(x,tuple):
    return iftrue(*x)
  else:
    return iffalse(x)


