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

# Chunks = Tuple[List[str],List[str]]      # (seen, rest)
# ParseData  = Either[str,Tuple[Chunks,Any]]
# Parser = Callable[[str],ParseData]

from pymonad.Either import Left, Right
from eitherutil import fold
from f import curry, fapply

def parse(formatter, parser, url):
  """
  Note formatter is auto-curried, so you don't have to pass in a curried func.
  """
  parsed = parser( ([], url.split('/')), curry(formatter) )
  return fold(
    lambda msg: Left(msg),
    lambda ((_,rest),result): (
      Right(result) if len(rest) == 0 or rest == [""]
      else Left("Parsed URL, but '%s' was left over" % "/".join(rest))
    ),
    parsed
  )


def segment(text):
  # type: Parser

  def _segment((seen,rest),result):
    # type: Tuple[Chunks,Any] -> ParseData

    if len(rest) == 0:
      return Left("Got to the end of the URL but wanted '%s'" % text)
    else:
      if rest[0] == text:
        return Right( ((seen + [rest[0]], rest[1:]), result) )
      else:
        return Left( "Wanted '%s' but got '%s'" % (text, "/".join(rest)) )

  return _segment

# short alias
s = segment

def custom(label,fn):
  # type: String -> Callable([str],Either[str,Any]) -> Parser

  def _custom((seen,rest), result):
    if len(rest) == 0:
      return Left("Got to the end of the URL but wanted '%s'" % label)
    else:
      chunk = rest[0]
      return fold(
        lambda msg: Left("Parsing '%s' failed: %s" % (chunk, msg)) ,
        lambda x:   Right( ((seen + [chunk], rest[1:]), result(x)) ),
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


def combine(pfirst,prest):
  # type: Parser -> Parser -> Parser

  @curry
  def _combine(chunks, ffirst):
    return (
      pfirst(chunks,ffirst) >> fapply(prest)
    )
  return _combine


def combine_all(parsers):
  # type: List[Parser] -> Parser

  """
  Note: added this for ease of use in Python, which doesn't have generic infix
  operators and flexible operator order, as in Elm.
  """
  return reduce(combine, parsers, lambda chunks,fn: Right((chunks,fn)) )

parts = combine_all


def one_of(parsers):  
  # type: List[Parser] -> Parser

  @curry
  def _one_of(choices, chunks, formatter):
    if len(choices) == 0:
      return Left("No parser worked")
    else:
      parser = choices[0]
      parsed = parser(chunks,formatter)
      return fold(
        lambda err: _one_of(choices[1:], chunks, formatter),
        lambda x:   Right(x),
        parsed
      )
      
  return _one_of(parsers)


def format(formatter, parser):
  # type: Any -> Parser -> Parser

  def _format(chunks,fn):
    parsed = parser(chunks, formatter)
    return fold(
      lambda err:             Left(err),
      lambda (newchunks,val): Right((newchunks, fn(val))),
      parsed
    )

  return _format

