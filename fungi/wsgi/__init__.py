import logging
from json import JSONEncoder
from webob import Request, Response, exc

from pymonad_extra.util.either import to_task, with_default
from ..util.f import curry, merge, assoc, dissoc, identity
from ..util.json_ import pretty_encode, encode_with
from ..util.err import reject_errors

from . import response

log = logging.getLogger(__name__)
def debug_log(msg,x):
  log.debug("%s : %s" % (msg,x))
  return x


# --- Response adapters

@curry
def from_string((ctype,charset),s):
  # (String, String) -> String -> (Dict, Op) 
 
  status = 200
  return (
    { 'status': status, 
      'content_type': ctype, 
      'charset': charset,
      'body': unicode(s)     # webob handles encoding
    },
    response.no_op()
  )
  

from_html = from_string(('text/html','utf8'))
from_text = from_string(('text/plain', 'utf8'))

@curry
def encode_json_with(encoder,data):
  # JSONEncoder -> Dict -> Task Exception (Dict, Op)

  from_json_s = from_string(('application/json','utf8'))
  return (
    to_task(encode_with(encoder,data))
      .fmap(lambda s: 
        from_json_s( debug_log("encode_json_with",s) )
      )
  )

encode_json = encode_json_with(JSONEncoder)


@curry
def template(spec,func,data):
  # (String, String) -> (Dict -> String) -> Dict -> Task Exception (Dict, Op)
  
  ctype, charset = spec
  from_s = from_string((ctype,charset))
  return (
    render(func,data).fmap(from_s)
  )

template_html = template(('text/html','utf-8'))
template_text = template(('text/plain','utf-8'))

# Note: use this as success case
def redirect_to(url):
  # String -> (Dict, Op)
  return (
    {'status': 303}, 
    response.add_header('Location',url) 
  )

# Note: use this as failure case
def redirect_response(url):
  return exc.HTTPSeeOther(location=url)


# --- Helpers for response finalizers

@curry
def finalize_after(fn, (a, op)):
  # ( a -> Task Exception (Dict, Op) ) -> 
  # (a, ResponseOp) -> 
  # Task Exception (Dict, Op)
  return (
    fn(a).fmap(
      lambda (newstate, newop): ( newstate, op + newop ) 
    )
  )

@curry
def and_finalize(newop, (a,op)):
  return (a, op + newop)

def and_add_header(k,v):
  return and_finalize(response.add_header(k,v))

def and_add_headers(pairs):
  return and_finalize(response.add_headers(pairs))

def and_set_cookie(p,c):
  return and_finalize(response.set_cookie(p,c))

and_gzip = and_finalize(response.gzip())

and_set_etag = and_finalize(response.set_etag())

def and_cache_control(opts):
  return and_finalize(response.cache_control(opts))

def and_cache_expires(secs):
  return and_finalize(response.cache_expires(secs))



# --- WSGI app adapter

def adapter(func):
  # (Request -> Task Exception (Dict, Op)) -> WSGIApp
  
  def _adapter(environ, start_response):
    def _finalize_error(resp):
      state['response'] = resp

    def _finalize_success((resp, op)):
      try:
        response.finalize(op, resp)
        state['response'] = resp
      except Exception as e:
        log.error(
          u'finalize: failed to execute %s' % (op,) ,
          extra={'error': e}
        )
        state['response'] = build_error_response(e)

    req = Request(environ)
    state = {"response": exc.HTTPNotImplemented() }

    task = func(req).bimap(
      build_error_response,
      (lambda (d,op): ( build_success_response(d), op ))
    )

    task.fork(_finalize_error, _finalize_success)
    return state['response'](environ, start_response)

  return _adapter


def build_error_response(e):
  # Exception -> HTTPError

  try:
    log.error(
      u'build_error_response: %s', 
      unicode(e), 
      extra={'error': e} 
    )
    if isinstance(e,exc.HTTPError) or isinstance(e,exc.HTTPRedirection):
      return e
    else:
       # Note: assumes ASCII repr of error
      tmpl = '${explanation}<br/><br/><pre>${detail}</pre>${html_comment}'
      return exc.HTTPInternalServerError(detail=str(e), body_template=tmpl)  
      
  except Exception as e_:
    return (
      exc.HTTPInternalServerError(
        detail="Error in building error response", comment=str(e_)
      )
    )

def build_success_response(attrs):
  # Dict -> WSGIApp

  try:
    attrs = merge(attrs, {'status': 200})
    attrs_ = dissoc('body',attrs)
    log.debug(
      'build_success_response: (body omitted)\n%s' % 
        with_default({}, pretty_encode(attrs_)), 
      extra={'response': attrs_}
    ) 
    resp = Response(**attrs)
    log.info(
      'build_success_response: %s' % attrs.get('status'),  
      extra={'status': attrs.get('status')}
    )     # TODO a little more info
    return resp

  # TODO: include backtrace
  except Exception as e:
    return build_error_response( 
      exc.HTTPInternalServerError(
        detail="Error in building response", comment=str(e)
      )
    )

# --- utils

# Note: as standalone function, Either would make more sense. But easier
# to deal with as a Task here.

@reject_errors
def render(fn,data):
  return fn(data)

