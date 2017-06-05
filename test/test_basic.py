import unittest
import logging
logging.basicConfig(level=logging.DEBUG)

from webtest import TestApp
from pymonad_extra.util.task import resolve, reject

import fungi
from fungi.wsgi import from_text, template_html, encode_json, and_gzip, and_set_etag, and_set_cookie
from fungi.parse import one_of, format, like
from fungi.util.adt import Type, match

def render(tmpl):
  def _render(d):
    return tmpl % d
  return _render

class SuccessNoConfigTests(unittest.TestCase):

  def setUp(self):
    self.app = TestApp( test_app_success_no_config() )
  
  def assert_success(self,content_type,resp):
    self.assertEqual(resp.status_int, 200)
    self.assertEqual(resp.content_type, content_type)

  def assert_gzip(self,resp):
    pass  # can't do much here because webtest decodes automatically

  def assert_has_etag(self,resp):
    self.assertIn('Etag', resp.headers, "Expected Etag in %s" % resp.headers)

  def test_success_text(self):
    resp = self.app.get("/text")
    self.assert_success("text/plain", resp)   

  def test_success_html(self):
    resp = self.app.get("/html")
    self.assert_success("text/html", resp)

  def test_success_json(self):
    resp = self.app.get(u"/json/cats/3")
    self.assert_success("application/json", resp)
    self.assert_has_etag(resp)


class FailNoConfigTests(unittest.TestCase):
   
  def setUp(self):
    self.app = TestApp( test_app_fail_no_config() )
  
  def assert_fail(self,status,resp):
    self.assertEqual(resp.status_int, status)

  def test_fail_text(self):
    resp = self.app.get("/text", status="*")
    self.assert_fail(500,resp)

  def test_fail_html(self):
    resp = self.app.get("/html", status="*")
    self.assert_fail(403,resp)

  def test_fail_json(self):
    resp = self.app.get("/json/thing/143", status="*")
    self.assert_fail(500,resp)




# --- routes

Text = Type("Text", [])
Html = Type("Html", [])
Json = Type("Json", [str, int])  # not sure why str and not unicode; webtest?

Routes = [Text, Html, Json]

RouteParser = (
  one_of([
    format( Text, like(u"GET /text") ),
    format( Html, like(u"GET /html") ),
    format( Json, like(u"GET /json/%s/%d") )
  ])
)


# --- test apps

def test_app_success_no_config():
  def _text(req):
    return resolve("Hello World").fmap(from_text) 
    
  def _html(req):
    return (
      ( resolve({"addressee": "world"})
          >> ( template_html( 
                 render("<html><body><h1>Hello %(addressee)s</h1></body></html>")
               )
             ) )
          .fmap( and_gzip )
    )

  def _json(s,i,req):
    return (
      resolve({"a": "hello", "b": "world", s: i})
        >> encode_json
    ).fmap( and_set_etag ).fmap( and_gzip )

  return test_app_no_config(_text, _html, _json)


def test_app_fail_no_config():

  def _text(req):
    return (
      ( resolve("Hello world")
          >> (lambda s: reject( AssertionError("Boom") )) )
          .fmap( from_text )
    )

  def _html(req):
    return (
      reject( fungi.exc.HTTPForbidden() )
        >> ( template_html( 
               render("<html><body><h1>Hello %(addressee)s</h1></body></html>")
             )
           )
    )

  # Note: fails json encode -> status = 500
  def _json(s,i,req):
    return (
      resolve({"a": "hello", "b": "world", type(None): s})
        >> encode_json
    )

  return test_app_no_config(_text, _html, _json)


def test_app_no_config( text, html, json ):
  return (
    fungi.mount( 
      RouteParser,
      (lambda req:
        match( Routes, {
          Text: (lambda : text(req) ),
          Html: (lambda : html(req) ),
          Json: (lambda s, i: json(s,i,req) )
        })
      )
    )
  )

if __name__ == '__main__':
  unittest.main()

