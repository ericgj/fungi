"""
This is a direct translation of Elm's url-parser into Python:
  https://github.com/evancz/url-parser

With much looser (and incomplete) type checking, as can be expected.

-----
Copyright (c) 2016, Evan Czaplicki
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the {organization} nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""


from pymonad.Either import Left, Right
from eitherutil import fold
from f import curry, fapply

def parse(formatter, parser, req):
  """
  Note formatter is auto-curried, so you don't have to pass in a curried func.
  """
  url = req.path[1:]
  parsed = parser( ([], url.split('/')), req, curry(formatter) )
  return fold(
    lambda msg: Left(msg),
    lambda ((_,rest),req,result): (
      Right(result() if callable(result) else result) if len(rest) == 0 or rest == [""] else \
      Left("Parsed URL, but '%s' was left over" % "/".join(rest))
    ),
    parsed
  )


def segment(text):
  # type: Parser

  def _segment((seen,rest),req,result):

    if len(rest) == 0:
      return Left("Got to the end of the URL but wanted '%s'" % text)
    else:
      if rest[0] == text:
        return Right( ((seen + [rest[0]], rest[1:]), req, result) )
      else:
        return Left( "Wanted '%s' but got '%s'" % (text, "/".join(rest)) )

  return _segment

# short alias
s = segment

def custom(label,fn):

  def _custom((seen,rest), req, result):
    if len(rest) == 0:
      return Left("Got to the end of the URL but wanted '%s'" % label)
    else:
      chunk = rest[0]
      return fold(
        lambda msg: Left("Parsing '%s' failed: %s" % (chunk, msg)) ,
        lambda x:   Right( ((seen + [chunk], rest[1:]), req, result(x)) ),
        fn(chunk)
      )

  return _custom

string = custom("STRING", Right)

def to_int(x):
  try: 
    return Right(int(x)) 
  except ValueError as e: 
    return Left(unicode(e))

number = custom("NUMBER", to_int)


# Non-URL based parsing

def custom_req(label,fn):

  def _custom_req((seen,rest), req, result):
    if fn(req):
      return Right(((seen,rest), req, result))
    else:
      return Left("Request %s does not match" % label)
  return _custom_req

def method(meth):
  return custom_req("METHOD", lambda req: req.method == meth)

def methods(meths):
  return custom_req("METHOD", lambda req: req.method in meths)  




def combine(pfirst,prest):
  # type: Parser -> Parser -> Parser

  @curry
  def _combine(chunks, req, ffirst):
    return (
      pfirst(chunks,req,ffirst) >> fapply(prest)
    )
  return _combine


def all_of(parsers):
  # type: List[Parser] -> Parser

  """
  Note: added this for ease of use in Python, which doesn't have generic infix
  operators and flexible operator order, as in Elm.
  """
  return reduce(combine, parsers, lambda chunks,req,fn: Right((chunks,req,fn)) )


def one_of(parsers):  
  # type: List[Parser] -> Parser

  @curry
  def _one_of(choices, chunks, req, formatter):
    if len(choices) == 0:
      return Left("No parser worked")
    else:
      parser = choices[0]
      parsed = parser(chunks,req,formatter)
      return fold(
        lambda err: _one_of(choices[1:], chunks, req, formatter),
        lambda x:   Right(x),
        parsed
      )
      
  return _one_of(parsers)


def format(formatter, parser):
  # type: Any -> Parser -> Parser

  def _format(chunks,req,fn):
    parsed = parser(chunks, req, formatter)
    return fold(
      lambda err:             Left(err),
      lambda (newchunks,r,v): Right((newchunks, r, fn(v))),
      parsed
    )

  return _format

