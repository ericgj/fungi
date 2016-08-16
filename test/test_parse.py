import unittest
import logging
from itertools import permutations

from fungi.util.f import identity

import fungi.parse as p
from fungi.util.adt import Type
import pymonad_extra.util.either as either

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class DummyRequest():
  def __init__(self, method, path):
    self.method = method
    self.path = path


class TestParse(unittest.TestCase):

  def assert_success(self, exp, parser, req):
    def _fail(msg):
      self.assertTrue( 
        False, "Expected success, was failure (message = %s)" % act.value )

    def _success(a):
      self.assertEqual(a,exp, 
        "Expected %s, was %s" % (a, exp) )

    act = parser(req)
    return either.fold( _fail, _success, act )

  def assert_fail(self, parser, req):
    def _fail(msg):
      self.assertTrue(True)

    def _success(a):
      self.assertFalse(
        True, "Expected failure, was success (value = %s)" % (a,))

    act = parser(req)
    return either.fold( _fail, _success, act )


  def test_all_of_path_segments(self):
    parsers = [ p.s("a"), p.string, p.s("b"), p.number ]
    formatter = Type("Formatter", [str, int])
    tester = p.parse( formatter, p.all_of(parsers) )

    # success parsing
    self.assert_success( 
      formatter("foo",12), tester, DummyRequest("GET", "/a/foo/b/12") )

    # success parsing with trailing /
    self.assert_success( 
      formatter("bar",13), tester, DummyRequest("GET", "/a/bar/b/13/") )

    # failed parsing
    self.assert_fail(
      tester, DummyRequest("GET", "/a/foo/b/bar") )

    # too short
    self.assert_fail(
      tester, DummyRequest("GET", "/a/foo/b") )

    # too long
    self.assert_fail(
      tester, DummyRequest("GET", "/a/foo/b/23/bar") )


  def test_all_of_with_method(self):
    parsers = [ p.s("x"), p.number, p.string, p.method("POST") ]
    formatter = Type("Formatter", [int, str])
    tester = p.parse( formatter, p.all_of(parsers) )

    # success
    self.assert_success(
      formatter(12,"foo"), tester, DummyRequest("POST", "/x/12/foo") )

    # failed to match method
    self.assert_fail(
      tester, DummyRequest("GET", "/x/12/foo") )


  def test_one_of(self):
    parsers = [ p.s("one"), p.s("two"), p.s("three") ]
    formatter = Type("Formatter", [])
    
    # all permutations
    testers = [
      p.parse( formatter, p.one_of(parsers_n) ) for parsers_n in permutations(parsers)
    ]

    n = 0
    for tester in testers:

      # success on matching any of the choices
      self.assert_success(
        formatter(), tester, DummyRequest("GET", "/two") )

      self.assert_success(
        formatter(), tester, DummyRequest("GET", "/one") )

      self.assert_success(
        formatter(), tester, DummyRequest("GET", "/three") )
      
      
      # fail on too short
      self.assert_fail(
        tester, DummyRequest("GET", "/") )

      # fail on no parser match
      self.assert_fail(
        tester, DummyRequest("GET", "/four") )

      # fail on too long
      self.assert_fail(
        tester, DummyRequest("GET", "/one/two") )

      # fail on too long and out of order
      self.assert_fail(
        tester, DummyRequest("GET", "/two/one") )

      n = n + 1
    
    print "Note: %d permutations tested" % n



  def test_complex(self):
    Home = Type("Home",[])
    GetThing = Type("GetThing",[int])
    PostThing = Type("PostThing",[])
    PutThing = Type("PutThing",[int])
    GetSubThing = Type("GetSubThing", [int,str])
    PostSubThing = Type("PostSubThing", [int])
    PutSubThing = Type("PutSubThing", [int,str])
    Three = Type("Three", [str,int,str])

    parsers = [ 
      p.format( Home, p.s("") ),
      
      p.format( GetThing,  
                p.all_of( [p.method("GET"), p.s("thing"), p.number] ) ),
      
      p.format( PostThing,
                p.all_of( [p.method("POST"), p.s("thing")] ) ),
      
      p.format( PutThing,
                p.all_of( [p.method("PUT"), p.s("thing"), p.number] ) ),
      
      p.format( GetSubThing,
                p.all_of( [p.method("GET"), p.s("thing"), p.number, p.s("sub"), p.string] ) ),

      p.format( PostSubThing,
                p.all_of( [p.method("POST"), p.s("thing"), p.number, p.s("sub")] ) ),
      
      p.format( PutSubThing,
                p.all_of( [p.method("PUT"), p.s("thing"), p.number, p.s("sub"), p.string] ) ),
      
      p.format( Three,
                p.all_of( [p.string, p.number, p.string] ) )
    ]

    tester = p.parse( identity, p.one_of(parsers) )
    
    # success on first matching
    self.assert_success(
      PostSubThing(123), tester, DummyRequest("POST", "/thing/123/sub") )

    # TODO more ?


  def test_complex_with_permutations(self):
    Home = Type("Home",[])
    GetThing = Type("GetThing",[int])
    GetSubThing = Type("GetSubThing", [int,str])
    PostSubThing = Type("PostSubThing", [int])

    parsers = [ 
      p.format( Home, p.s("") ),
      
      p.format( GetThing,  
                p.all_of( [p.method("GET"), p.s("thing"), p.number] ) ),
      
      p.format( GetSubThing,
                p.all_of( [p.method("GET"), p.s("thing"), p.number, p.s("sub"), p.string] ) ),

      p.format( PostSubThing,
                p.all_of( [p.method("POST"), p.s("thing"), p.number, p.s("sub")] ) )
    ]

    # all permutations
    testers = [
      p.parse( identity, p.one_of(parsers_n) ) for parsers_n in permutations(parsers)
    ]
    
    n = 0
    for tester in testers:

      self.assert_success(
        Home(), tester, DummyRequest("GET", "/") )

      self.assert_success(
        GetThing(987), tester, DummyRequest("GET", "/thing/987") )

      self.assert_success(
        GetSubThing(654, "foo"), tester, DummyRequest("GET", "/thing/654/sub/foo") )

      self.assert_success(
        PostSubThing(123), tester, DummyRequest("POST", "/thing/123/sub") )

      self.assert_fail(
        tester, DummyRequest("POST", "/thing/123/") )

      n = n + 1
    
    print "Note: %d permutations tested" % n


  def test_like(self):
    PutSubThing = Type("PutSubThing", [int,str])
    parser = p.like("PUT /thing/%d/sub/%s")
      
    tester = p.parse(PutSubThing, parser)

    self.assert_success(
      PutSubThing(123,'baz'), tester, DummyRequest("PUT", "/thing/123/sub/baz") )

    self.assert_fail(
      tester, DummyRequest("GET", "/thing/123/sub/baz") )

    self.assert_fail(
      tester, DummyRequest("PUT", "/thing/baz/sub/123") )


if __name__ == '__main__':
  unittest.main()

