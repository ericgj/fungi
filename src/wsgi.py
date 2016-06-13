
@curry
def adapter(log,func):
  def _adapter(environ, start_response):
    def _respond(resp):
      return resp(environ, start_response)

    req = Request(environ)
    reqlog = log(**req.__dict__)  # TODO may need to scrub attributes 
    task = func(req).bimap(
      build_error_response(reqlog),
      build_success_response(reqlog)
    )
    task.fork(_respond)

  return _adapter


@curry
def build_error_response(log,e):
  try:
    log.error(e)
    if isinstance(e,exc.HTTPError):
      return e
    else:
      return exc.HTTPServerError(comment=str(e))
      
  except Exception as e:
    return exc.HTTPServerError(detail="Error in building error response", comment=str(e))

@curry
def build_success_response(log,attrs):
  cookies = {}
  if isinstance(attrs,tuple):
    attrs, cookies = attrs
  try:
    log.debug(response=attrs)               # TODO scrub
    log.info(response=attrs.get('status'))   # TODO a little more info
    resp = Response(**attrs)
    # TODO cookies
  except Exception as e:
    return build_error_response( log,
      exc.HTTPServerError(detail="Error in building response", comment=str(e))
    )

