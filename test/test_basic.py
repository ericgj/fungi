from __future__ import print_function 
import unittest
import logging
logging.basicConfig(level=logging.DEBUG)

from webtest import TestApp
from pymonad_extra.util.task import resolve, reject
from adt import Type, match

import fungi
from fungi.wsgi import (
  from_text, template_html, encode_json, 
  write_csv_tuples, write_csv_dicts, write_tsv_tuples, write_tsv_dicts,
  write_dsv_tuples, write_dsv_dicts,
  and_gzip, and_set_etag, and_set_cookie, and_cache_control, and_cache_expires,
  and_add_header, and_add_headers
)
from fungi.parse import one_of, format, like
from fungi.cookies import signed_profile, unsigned_profile, cookie

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

  def assert_has_cookie(self,resp):
    self.assertIn('Set-Cookie', resp.headers, "Expected Set-Cookie in %s" % resp.headers)

  def assert_gzip(self,resp):
    pass  # can't do much here because webtest decodes automatically

  def assert_has_etag(self,resp):
    self.assertIn('Etag', resp.headers, "Expected Etag in %s" % resp.headers)

  def assert_has_header(self,expkey,expval,resp):
    self.assertIn(expkey, resp.headers, "Expected header %s in %s" % (expkey, resp.headers) )
    self.assertEqual(resp.headers.get(expkey,None), expval)

  def assert_cache_expires(self,resp):
    self.assertIn('Expires', resp.headers, "Expected Expires in %s" % resp.headers)

  def assert_cache_control(self,resp):
    self.assertIn('Cache-Control', resp.headers, "Expected Cache-Control in %s" % resp.headers)

  def test_success_text(self):
    resp = self.app.get("/text")
    print(resp)
    self.assert_success("text/plain", resp)
    self.assert_has_cookie(resp)
    self.assert_cache_expires(resp)
    self.assert_cache_control(resp)

  def test_success_html(self):
    resp = self.app.get("/html")
    print(resp)
    self.assert_success("text/html", resp)

  def test_success_json(self):
    resp = self.app.get(u"/json/cats/3")
    print(resp)
    self.assert_success("application/json", resp)
    self.assert_has_etag(resp)
    self.assert_has_header("X-FOO","FOO",resp)
    self.assert_has_header("X-BAR","BAR",resp)
    self.assert_has_header("X-QUUX","QUUX",resp)

  def test_success_csv(self):
    resp = self.app.get(u'/csv')
    print(resp)
    self.assert_success("text/csv", resp)

  def test_success_dsv(self):
    resp = self.app.get(u'/dsv')
    print(resp)
    self.assert_success("text/x-pipe-delimited", resp)



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

  def test_fail_csv(self):
    resp = self.app.get("/csv", status="*")
    self.assert_fail(500,resp)

  def test_fail_dsv(self):
    resp = self.app.get("/dsv", status="*")
    self.assert_fail(500,resp)



# --- routes

Text = Type("Text", [])
Html = Type("Html", [])
Json = Type("Json", [str, int])  # not sure why str and not unicode; webtest?
Csv = Type("Csv", [])
Dsv = Type("Dsv", [])

Routes = [Text, Html, Json, Csv, Dsv]

RouteParser = (
  one_of([
    format( Text, like(u"GET /text") ),
    format( Html, like(u"GET /html") ),
    format( Json, like(u"GET /json/%s/%d") ),
    format( Csv, like(u"GET /csv") ), 
    format( Dsv, like(u"GET /dsv") )
  ])
)


# --- test apps

def test_app_success_no_config():
  
  sprofile = signed_profile(u"secret",u"salt",{u"secure": True})
  uprofile = unsigned_profile({u"path": "/foo"})

  def _text(req):
    return (
      resolve("Hello World")
        .fmap(from_text)
        .fmap( and_set_cookie(sprofile,cookie(u"user",{u"name": u"Eric"})) ) 
        .fmap( and_set_cookie(uprofile,cookie(u"foo",{u"name": u"Foo"})) ) 
        .fmap( and_cache_expires(60) )
        .fmap( and_cache_control({"s-maxage": 3600, "proxy-revalidate": None}) )
    )
    
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
      ( resolve({"a": "hello", "b": "world", s: i})
          >> encode_json
      ).fmap( and_set_etag )
       .fmap( and_gzip )
       .fmap( and_add_header("X-FOO","FOO") )
       .fmap( and_add_headers([("X-BAR","BAR"),("X-QUUX","QUUX")]) )
    )

  def _csv(req):
    return (
      resolve([{"a": "1", "b": "2"}, {"a": "1,1", "b": "2,2"}, {"a": "1,1\n1", "b": "2,2\n2"}])
        .fmap( write_csv_dicts(["a","b"]) )
    )

  def _dsv(req):
    return (
      resolve([{"a": "1", "b": "2"}, {"a": "1,1", "b": "2,2"}, {"a": "1,1\n1", "b": "2,2\n2"}])
        .fmap( 
          write_dsv_dicts(
            'text/x-pipe-delimited', 
            {'dialect': 'excel-tab', 'delimiter': '|'},
            ["a","b"]
          ) 
        )
    )

  return test_app_no_config(_text, _html, _json, _csv, _dsv)


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

  def _csv(req):
    return (
      ( resolve([{"a": 1, "b": 2}, {"a": 11, "b": 22}, {"a": 111, "b": 222}])
          >> reject( AssertionError("Boom!") ) ) 
          .fmap( write_csv_tuples(["a","b"]) )
    )

  def _dsv(req):
    return (
      ( resolve([{"a": "1", "b": "2"}, {"a": "1,1", "b": "2,2"}, {"a": "1,1\n1", "b": "2,2\n2"}])
          >> reject( AssertionError("Boom |") ) ) 
        .fmap( 
          write_dsv_dicts(
            'text/x-pipe-delimited', 
            {'dialect': 'excel-tab', 'delimiter': '|'},
            ["a","b"]
          ) 
        )
    )

  return test_app_no_config(_text, _html, _json, _csv, _dsv)


def test_app_no_config( text, html, json, csv, dsv ):
  return (
    fungi.mount( 
      RouteParser,
      (lambda req:
        match( Routes, {
          Text: (lambda : text(req) ),
          Html: (lambda : html(req) ),
          Json: (lambda s, i: json(s,i,req) ),
          Csv: (lambda : csv(req) ),
          Dsv: (lambda : dsv(req) )
        })
      )
    )
  )

if __name__ == '__main__':
  unittest.main()

