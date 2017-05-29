import sys
import os
import os.path
sys.path.insert(1, os.path.join( os.environ.get('GAE_SDK_ROOT',''), 'lib/yaml/lib') )
import json
from urlparse import parse_qs

import unittest
import logging
logging.basicConfig(level=logging.DEBUG)

import httplib2
from webtest import TestApp
from google.appengine.ext.testbed import Testbed
from google.appengine.api import users
from pymonad.Maybe import Nothing
from pymonad_extra.util.task import reject, resolve

from fungi import mount
from fungi.wsgi import encode_json
import fungi.oauth as oauth
from fungi.util.f import always, fapply
from fungi.util.adt import Type, match
from fungi.parse import one_of, s, format, method
from fungi.gae.oauth import CredentialsStore
from fungi.gae.user import current_or_redirect_to_login
import fungi.util.err as err

# decorators, maybe move to pymonad_extra.util.task ? 
def reject_errors(fn):
  # (*a -> b) -> Task Exception b
  def _reject(*a,**kw):
    try:
      return resolve( fn(*a,**kw) )
    except Exception as e:
      return reject( err.wrap(e) )
  return _reject
      
def reject_errors_task(fn):
  # (*a -> Task Exception c) -> Task Exception c
  def _reject(*a,**kw):
    try:
      return fn(*a,**kw)
    except Exception as e:
      return reject( err.wrap(e) )
  return _reject

#-------------------------------------------------------------------------------
# Infrastructure fakery, a necessary evil
# most of this copied with slight changes from oauth2client appengine tests
#-------------------------------------------------------------------------------

def set_http_mock():
  orig = httplib2.Http
  httplib2.Http = Http2Fake
  return orig

def reset_http(orig):
  httplib2.Http = orig

def set_user_mock():
  orig = users.get_current_user
  users.get_current_user = UserFake
  return orig

def reset_user(orig):
  users.get_current_user = orig


class UserFake(object):
  def user_id(self):
    return 'fakeuser@fake.com'

class Http2Fake(object):
  status = 200
  content = {
    'access_token': 'dummy-access-token',
    'refresh_token': 'dummy-refresh-token',
    'expires_in': 3600,
    'extra': 'some extra value'
  }

  def request(self,token_uri,method,body,headers,*args,**kwargs):
    self.body = body
    self.headers = headers
    return (self, json.dumps(self.content))


#-------------------------------------------------------------------------------

class TestAppEngineOAuth(unittest.TestCase):

  def setUp(self):
    tb = Testbed()
    tb.activate()
    tb.init_datastore_v3_stub()
    tb.init_memcache_stub()
    tb.init_user_stub()
    self.testbed = tb

    self.orig_http = set_http_mock()
    self.orig_user = set_user_mock()
    
    self.current_user = users.get_current_user()
    self.secret = 'xsrfsecret123'
    self.cache = CredentialsStore()
    self.clear_cache()
    
  def tearDown(self):
    self.testbed.deactivate()
    reset_http(self.orig_http)
    reset_user(self.orig_user)

    
  def assertResponseRedirect(self,data):
    act = data.get('status')
    self.assertTrue( act in [302,303,307], "Expected redirect response, got status==%s" % str(act) )
    
  def assertResponseLocation(self,exp,data):
    hdrs = data.get('headerlist',[])
    try:
      act = next( v for (k,v) in hdrs if k == 'Location' )
    except StopIteration:
      raise AssertionError, "No Location header in response"
    act = act.split('?',1)[0]
    self.assertEqual(act, exp, "Expected Location to be '%s', was '%s'" % (exp,act) )

  def assertResponseLocationParam(self,key,exp,data):
    hdrs = data.get('headerlist',[])
    try:
      loc = next( v for (k,v) in hdrs if k == 'Location')
    except StopIteration:
      raise AssertionError, "No Location header in response"
    q = parse_qs(loc.split('?',1)[1])
    act = q.get(key)[0]
    self.assertEqual(act, exp, 
      "Expected Location query param '%s' to be '%s', was '%s'" % (key,exp,act)
    )

  def clear_cache(self):
    def _raise(e):
      raise e
    def _log(xs):
      log.info("%d credentials deleted" % len(xs))

    log = logging.getLogger(self.__class__.__name__ + '.clear_cache')
    if self.cache:
      self.cache.delete_all().fork(_raise, _log)


  #-------- Test app

  def app(self, oauth_params):
    
    Required = Type('Required',[])
    Callback = Type('Callback',[])
    Routes = ( Required, Callback )
    
    encode_path = (
      match(Routes, {
        Required: always("/required"),
        Callback: always("/oauth2callback")
      })
    )

    def encode_url(route, req):
      return req.relative_url(encode_path(route))

    route_parser = (
      one_of([
        format( Required, s("required") ),
        format( Callback, s("oauth2callback") )
      ])
    )

    def route(req):
      return (
        match(Routes, {
          Required: always(required_handler(req)),
          Callback: always(callback_handler(req)) 
        })
      )

    def required_handler(req):
      @reject_errors_task
      def _handler(http, reauth, req):
        testcase.assertIsNotNone(http)
        testcase.assertIsNotNone(reauth)
        testcase.was_authorized = True
        return encode_json({'reauth': reauth})

      return _oauth_required(req) >> fapply(_handler)

    def callback_handler(req):
      @reject_errors
      def _spy(respdata):
        testcase.assertResponseRedirect(respdata)
        testcase.assertResponseLocation(encode_url(Required(),req), respdata)
        key = oauth_params.token_response_param
        if key:
          testcase.assertResponseLocationParam(
            key, json.dumps(Http2Fake.content, separators=(',',':')), respdata
          )
        testcase.called_callback = True
        return respdata
      return _oauth_callback(req) >> _spy

    def _oauth_required(req):
      return (
        current_or_redirect_to_login(req.url).fmap(lambda u: u.user_id())
          >> oauth.authorize(oauth_params, testcase.cache, testcase.secret, req)
      )
    
    def _oauth_callback(req):
      return (
        current_or_redirect_to_login(req.url).fmap(lambda u: u.user_id())
          >> oauth.callback(oauth_params, testcase.cache, testcase.secret, req)
      )

    testcase = self
    testcase.was_authorized = False
    testcase.called_callback = False
 
    return mount( route_parser, route )


  #------- Tests

  def test_required(self):
    log = logging.getLogger(self.__class__.__name__ + '.test_required')
    
    params = oauth.OAuthParams(
      client_id='fake-client-id', client_secret='fake-client-secret', 
      scopes=['fake-scope-1', 'fake-scope-2'],
      user_agent='test',
      auth_uri='https://fake.com/oauth',
      token_uri='https://fake.com/oauth/token',
      revoke_uri='https://fake.com/oauth/revoke',
      callback_path='/oauth2callback',
      token_response_param='token_response',
      flow_params={}
    )
  
    app = TestApp(
      self.app(params), 
      extra_environ={
        'wsgi.url_scheme': 'http',
        'HTTP_HOST': 'localhost'
      }
    )

    # 1. initial request to OAuth-required endpoint should be a redirect
    #    to start the OAuth dance.
    #
    response = app.get('http://localhost/required')
    log.info("Initial response:\n----------\n%s\n---------\n" % response)
    self.assertEqual(False, self.was_authorized, "Expected not authorized, but was authorized")

    # 2. simulate callback 
    #
    
    state = _location_url_param('state', response)
    log.debug("XSRF-protected state: %s" % state)

    response = app.get(
      'http://localhost/oauth2callback', 
      { 'code':  'xyz_access_code', 'state': state }
    )

    log.info("Callback response:\n----------\n%s\n----------\n" % response)
    self.assertTrue(self.called_callback, "Callback not called")

    # 3. now request should proceed with credentials stored
    #
    response = app.get('/required')
    log.info("Response after callback:\n----------\n%s\n---------\n" % response)
    self.assertEqual(True, self.was_authorized, "Expected authorized, but not authorized")


#----- Utils

def _location_url_param(p, resp):
  q = parse_qs(resp.headers['Location'].split('?',1)[1])
  return q.get(p)[0]



if __name__ == '__main__':
  unittest.main()

