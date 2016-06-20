import json
from google.appengine.api import memcache

from f import curry
from pymonad.Either import Left, Right
from eitherutil import to_task
from taskutil import pass_through
import err

@curry
def put(encoder, timeout, key, val): 
  # JSONEncoder -> Int -> String -> a -> Task Exception None

  def _putstr(s):
    def _put(rej,res):
      try:
        memcache.add(key=key, value=s, time=timeout)
        res(None)
      except Exception as e:
        rej(err.wrap(e))

    return Task(_put)

  return to_task(json_encode(encoder, val)) >> _putstr


@curry
def get(decoder, key):
  # JSONDecoder -> String -> Task Exception (Either Exception a)

  def _get(rej,res):
    try:
      raw = memcache.get(key)
      res( Left(KeyError("Memcache key not found or expired: %s" % key)) \
           if raw is None else \
           Right(raw) 
      )
    except Exception as e:
      rej( err.wrap(e) )

  return Task(_get).fmap(lambda m: m.fmap( json_decode(decoder) ))


@curry
def get_from_cookie(getter, decoder, ckey, req):
  # (String -> Request -> Task Exception String) 
  # -> JSONDecoder 
  # -> String 
  # -> Request 
  # -> Task Exception (String, a)
  def _get(skey):
    return get(decoder, skey) >> to_task
  return getter(ckey, req) >> pass_through(_get)


@curry
def json_encode(encoder, val):
  # JSONEncoder -> a -> Either Exception String

  try:
    return Right( json.dumps(val, cls=encoder, separators=(',',':')) )
  except Exception as e:
    return Left( err.wrap(e) )


@curry
def json_decode(decoder, s):
  # JSONDecoder -> String -> Either Exception a

  try:
    return Right( json.loads(s, cls=decoder) )
  except Exception as e:
    return Left( err.wrap(e) )


