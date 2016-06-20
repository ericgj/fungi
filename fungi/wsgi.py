import json
from webob import Request, Response, exc

from pymonad_extra import Task
from util.f import curry, merge, assoc, identity
import util.err

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
def encode_json(encoder,data):
  # JSONEncoder -> (Dict | (Dict,Cookies)) -> Task Exception (Dict | (Dict,Cookies))

  from_json_s = from_string(('application/json','utf8'))
  return _if_tuple(
    lambda d,c: json_encode(encoder,d).fmap(lambda s: (from_json_s(s),c)),
    lambda d:   json_encode(encoder,d).fmap(from_json_s),
    data
  )

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

  def _appendhdrs(a):
    assoc('headerlist', a, a.get('headerlist',[]) + hdrlist)

  return _if_tuple(
    lambda at,c: (_appendhdrs(at), c),
    lambda at:    _appendhdrs(at)    ,
    attrs
  )
    
def redirect_to(url):
  # String -> (Dict | (Dict,Cookies))
  return add_headers([('Location',url)], {'status': 303}) 


# --- WSGI app adapter

@curry
def adapter(log,func):
  # Logger -> (Request -> Task Exception Dict) -> WSGIApp
  
  def _adapter(environ, start_response):
    def _attach(resp):
      req.response = resp

    req = Request(environ)
    req.response = exc.HTTPNotImplemented()

    task = func(req).bimap(
      build_error_response(log),
      build_success_response(log)
    )
    task.fork(_attach, _attach)

    return req.response(environ, start_response)

  return _adapter

@curry
def adapter_with_cookies(log,writer,func):
  # Logger 
  # -> (Cookies -> Response -> Task Exception Response) 
  # -> (Request -> Task Exception (Dict,Cookies)) 
  # -> WSGIApp
  
  def _adapter(environ, start_response):
    def _build_and_save_cookies((attrs,cs)):
      resp = build_success_response(log,attrs)
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
          build_error_response(log),
          identity
        )
    )
    task.fork(_attach, _attach)

    return req.response(environ, start_response)

  return _adapter


@curry
def build_error_response(log,e):
  # Logger -> Exception -> HTTPError

  try:
    log.error('build_error_response: %s', unicode(e), extra={'error': e} )
    if isinstance(e,exc.HTTPError):
      return e
    else:
      return exc.HTTPInternalServerError(comment=str(e))   # Note: assumes ASCII repr
      
  except Exception as e_:
    return exc.HTTPInternalServerError(detail="Error in building error response", comment=str(e_))

@curry
def build_success_response(log,attrs):
  # Logger -> Dict -> WSGIApp

  try:
    attrs = merge({'status': 200}, attrs)
    log.debug('build_success_response', extra={'response': attrs})                 # TODO scrub
    resp = Response(**attrs)
    log.info('build_success_response',  extra={'status': attrs.get('status')})     # TODO a little more info
    return resp

  # TODO: include backtrace
  except Exception as e:
    return build_error_response( log,
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


def json_encode(encoder,data):
  def _encode(rej,res):
    try:
      res( json.dumps(data, cls=encoder, separators=(',',':')) )

    except Exception as e:
      rej(err.wrap(e))
  
  return Task(_encode)


def _if_tuple(iftrue,iffalse,x):
  if isinstance(x,tuple):
    return iftrue(*x)
  else:
    return iffalse(x)


