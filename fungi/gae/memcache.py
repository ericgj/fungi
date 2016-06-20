from google.appengine.api import memcache

from fungi.util.f import curry, always
from pymonad.Maybe import Nothing, Just
from pymonad_extra.util.maybe import with_default
from pymonad_extra import Task
from pymonad_extra.util.task import resolve
import fungi.util.err as err

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
def add(time, key, value):
  def _add(rej,res):
    try:
      res( memcache.add(key,value,time=time) )
    except Exception as e:
      rej( err.wrap(e) )
  return Task(_add)


@curry
def cache_get_with_time(time, key, task):
  # Int -> String -> Task a b -> Task a b

  def _and_add(r):
    return add(time,key,r).fmap(always(r))

  return (
    get(key) >> (
      lambda r: (
        with_default(
          task >> _and_add ,
          r.fmap(resolve)
        )
      )
    )
  )

cache_get = cache_get_with_time(0)


