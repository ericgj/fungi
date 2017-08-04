from google.appengine.api import memcache

from ..util.f import curry, always
from pymonad.Maybe import Nothing, Just
from pymonad_extra.util.maybe import with_default
from pymonad_extra.util.task import resolve

from ..util.err import reject_errors

class MemcacheAddFailure(Exception):
  def __init__(self,k,v):
    self.key = k
    self.value = v

  def __str__(self):
    return "Memcache failed to add value at key %s : %s" % (self.key, self.value)

@reject_errors
def get(key):
  # String -> Task Exception (Maybe a)
  r = memcache.get(key)
  return Nothing if r is None else Just(r)

@reject_errors
def get_multi(prefix, keys):
  # String -> List String -> Task Exception (List (Maybe a))
  r = memcache.get_multi(keys, key_prefix=prefix)
  return [ Nothing if r.get(k) is None else Just(r.get(k)) for k in keys ]

@curry
def add_with_time(time, key, value):
  @reject_errors
  def _add():
    r = None
    if time is None:
      r = memcache.add(key,value)
    else:
      r = memcache.add(key,value,time=time)

    if bool(r):
      return value
    else:
      raise MemcacheAddFailure(key,value)

  return _add()

add = add_with_time(None)

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

cache_get = cache_get_with_time(None)


