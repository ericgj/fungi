from google.appengine.api import memcache

from f import curry, always
from pymonad.Maybe import Nothing, Just
from taskmonad import Task
from taskutil import resolve
import err

def get(key):
  # String -> Task Exception (Maybe a)

  def _get(rej,res):
    try:
      r = memcache.get(key)
      res( Nothing if r is None else Just(r) )
    except Exception as e:
      rej( err.wrap(e) )
  return Task(_get)

def get_multi(prefix, keys):
  # String -> List String -> Task Exception (List (Maybe a))

  def _get_multi(rej,res):
    try:
      r = memcache.get_multi(keys, key_prefix=prefix)
      res( [ Nothing if r.get(k) is None else Just(r.get(k)) for k in keys ] )
    except Exception as e:
      rej( err.wrap(e) )
  return Task(_get_multi)

@curry
def cache_get_with_time(time, key, task):
  # Int -> String -> Task a b -> Task a b

  def _and_add(r):
    return add(time,key,r).fmap(always(r))

  return (
    get(key) >> (
      with_default(
        task >> _and_add, 
        resolve
      )
    )
  )

cache_get = cache_get_with_time(0)


