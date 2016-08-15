from collections import namedtuple
from urlparse import urlparse, parse_qsl, urlunparse
from urllib import urlencode

from webob import exc
from httplib2 import Http
from oauth2client import GOOGLE_AUTH_URI, GOOGLE_REVOKE_URI, GOOGLE_TOKEN_URI
from oauth2client.client import OAuth2WebServerFlow
import oauth2client.contrib.xsrfutil as xsrfutil

from pymonad.Maybe import Maybe, Nothing, Just
from pymonad.Either import Left, Right
from pymonad_extra.Task import Task
import pymonad_extra.util.maybe as maybe
import pymonad_extra.util.either as either

from util.f import curry, always 
from wsgi import redirect_to
import util.err as err
import util.json_ as json_

OAuthParams = namedtuple('OAuthParams', [
  'client_id',
  'client_secret',
  'scopes',
  'user_agent',
  'auth_uri',
  'token_uri',
  'revoke_uri',
  'callback_path',
  'token_response_param',  # or None
  'flow_params'
])

def GoogleOAuthParams(client_id,client_secret,scopes,user_agent,callback_path,token_response_param,flow_params):
  return (
    OAuthParams(
      client_id,
      client_secret,
      scopes,
      user_agent,
      GOOGLE_AUTH_URI,
      GOOGLE_TOKEN_URI,
      GOOGLE_REVOKE_URI,
      callback_path,
      token_response_param,
      flow_params
    )
  )


@curry
def authorize(params,cache,secret,req,uid):
  # OAuthParams -> 
  #   {get: id -> Task Exception (Maybe Credentials)} ->
  #   String -> 
  #   Request -> 
  #   id -> 
  #   Task (HttpRedirection | HTTPError) ((*a -> Http), String, Request)

  # note XSRF-protecting the original URL as the 'state' param
  # secret param is a site-wide XSRF secret key
  state = either.with_default(uid, xsrf_encode(secret,req.url,uid)) 
  flow = webserver_flow( params, req, {'state': state} )

  def _auth_creds(creds):
    def _auth(rej,res):
      try:
        if creds == Nothing:
          # if credentials not in cache,
          #   redirect to the flow authorize URL (step 1 of OAuth dance)
          #
          rej( exc.HTTPFound( location=str(flow.step1_get_authorize_url()) ) )
        
        else:
          # if credentials are in cache,
          #   resolve to (http, authurl, req)  where 
          #   - http is an httplib2 client authorized with the credentials.
          #   - authurl is the flow authorize URL
          #
          # Note that oauth2client.client.AccessTokenRefreshError should be 
          #   caught by downstream tasks where the authorized http is used, and 
          #   redirect to authurl. This is less than ideal.
          #
          res(( 
            authorized_http(creds.value), 
            flow.step1_get_authorize_url(),
            req
          ))

      except Exception as e:
        rej( err.wrap(e) )

    return Task(_auth)

  return cache.get(uid) >> _auth_creds


@curry
def callback(params,cache,secret,req,uid):
  # OAuthParams -> 
  #   {put: id -> Credentials -> Task Exception x} -> 
  #   String  ->
  #   Request -> 
  #   id -> 
  #   Task HTTPException Dict
  
  # Unless error,
  #   do the OAuth exchange to get credentials
  #   store the credentials in cache
  #   redirect to the originally requested URI, 
  #     as XSRF-protection-encoded in the 'state' param of credentials
  #

  def _exchange(rej,res):
    if req.params.has_key('error'):
      # if request has 'error' param, reject with Unauthorized error (401)
      # note I'm not sure about using this response
      #
      comment = req.params.get('error_description', req.params.get('error',''))
      rej( exc.HTTPUnauthorized(comment=comment) )

    else:
      # otherwise, resolve to credentials of OAuth exchange (step 2 of dance)
      #
      try:
        flow = webserver_flow(params,req,{})
        res( flow.step2_exchange(req.params) )
      except Exception as e:
        rej( err.wrap(e) )
       
  def _cache_and(creds):
    # Credentials -> Task Exception Credentials
    #
    return cache.put(uid,creds).fmap(always(creds))
     
  def _get_redirect(creds):
    # Credentials -> Task Exception String
    #
    uri = xsrf_decode(secret,req.params.get('state'), uid)
    return either.to_task( uri.fmap(_add_token_response(creds.token_response)) )

  @curry
  def _add_token_response(data,uri):
    # Dict -> String -> String
    #
    # if oauth has token_response_param,
    #   add the json-encoded token_response from credentials to the uri params
    #
    def _add(key):
      tok = either.with_default( '{}', json_.encode(data) )
      return add_query_param(uri, key, tok)
    
    if params.token_response_param is None:
      return uri
    else:
      return _add(params.token_response_param)

  return (
    (( Task(_exchange) 
         >> _cache_and) 
         >> _get_redirect)
         .fmap(redirect_to)
  )


def webserver_flow(params, req, extras):
  extra = dict( params.flow_params.items() + extras.items() )
  redirect_uri = req.relative_url(params.callback_path)
  return (
    OAuth2WebServerFlow(
      params.client_id, params.client_secret, params.scopes, 
      redirect_uri=redirect_uri, user_agent=params.user_agent,
      auth_uri=params.auth_uri, token_uri=params.token_uri,
      revoke_uri=params.revoke_uri, **extra
    )
  )

def authorized_http(creds):
  def _http(*args, **kwargs):
    return creds.authorize(Http(*args, **kwargs))  
  return _http


class InvalidXSRFTokenError(Exception):
  def __str__(self):
    return "Invalid XSRF token"

@curry
def xsrf_encode(secret, uri, uid):
  # String -> String -> id -> Either Exception Bytes

  # Note: returns a Python2 string (bytes)
  # Does not work with unicode URIs
  try:
    tok = xsrfutil.generate_token(secret,uid,action_id=str(uri))
    return Right(str(uri) + ':' + tok)
  except Exception as e:
    return Left(err.wrap(e))

@curry
def xsrf_decode(secret, state, uid):
  # String -> String -> id -> Either Exception Bytes

  # Note: returns URI as Python2 string (bytes)
  # Does not work with unicode URIs
  try:
    uri, tok = str(state).rsplit(':',1)
    if not xsrfutil.validate_token(secret,tok,uid,action_id=uri):
      raise InvalidXSRFTokenError()
    return Right(uri)
  except Exception as e:
    return Left(err.wrap(e))


def add_query_param(url, name, value):
  # note copied from oauth2client.util

  parsed = list(urlparse(url))
  q = dict(parse_qsl(parsed[4]))
  q[name] = value
  parsed[4] = urlencode(q)
  return urlunparse(parsed)


