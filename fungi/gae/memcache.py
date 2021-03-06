from google.appengine.api import memcache

from fungi.util.f import curry, always
from pymonad.Maybe import Nothing, Just
from pymonad_extra.util.maybe import with_default
from pymonad_extra.Task import Task
from pymonad_extra.util.task import resolve
import fungi.util.err as err

class MemcacheAddFailure(Exception):
  def __init__(self,k,v):
    self.key = k
    self.value = v

  def __str__(self):
    return "Memcache failed to add value at key %s : %s" % (self.key, self.value)


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
def add_with_time(time, key, value):
  def _add(rej,res):
    try:
      r = None
      if time is None:
        r = memcache.add(key,value)
      else:
        r = memcache.add(key,value,time=time)

      if bool(r):
        res( value )
      else:
        raise MemcacheAddFailure(key,value)

    except Exception as e:
      rej( err.wrap(e) )
  
  return Task(_add)

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


