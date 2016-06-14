from webob import Request, Response, exc
from f import curry, merge
noop = lambda x: None

def adapter(log,func):
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
def build_error_response(log,e):
  try:
    log.error('build_error_response: %s', unicode(e), extra={'error': e} )
    if isinstance(e,exc.HTTPError):
      return e
    else:
      return exc.HTTPInternalServerError(comment=str(e))
      
  except Exception as e:
    return exc.HTTPInternalServerError(detail="Error in building error response", comment=str(e))

@curry
def build_success_response(log,attrs):
  cookies = {}
  if isinstance(attrs,tuple):
    attrs, cookies = attrs
  try:
    attrs = merge({u'status_code': 200}, attrs)
    log.debug('build_success_response', extra={'response': attrs})                 # TODO scrub
    log.info('build_success_response',  extra={'status': attrs.get('status')})     # TODO a little more info
    resp = Response(**attrs)
    # TODO cookies
    return resp

  except Exception as e:
    return build_error_response( log,
      exc.HTTPInternalServerError(detail="Error in building response", comment=str(e))
    )

