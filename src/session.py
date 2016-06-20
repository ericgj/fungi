from functools import reduce
from typing import NamedTuple, Union, List, Dict, Any

from f import assoc, dissoc, always
from taskutil import to_maybe, resolve
from pymonad.Maybe import Just, Nothing
from maybeutil import with_default
from unionutil import match

from cookie import Cookie

SessionPut = NamedTuple('SessionPut', [('key', unicode), ('value', Any)])
SessionRm = NamedTuple('SessionRm', [('key', unicode)])
SessionClear = NamedTuple('SessionClear', [])
SessionTx = Union[SessionPut, SessionRm, SessionClear]
Session = NamedTuple('Session', [
            ('cookie', Cookie), ('data', Dict), ('tx', List[SessionTx])
          ])

def get_or_create(getter, creator, ckey, request):
  # (String -> Request -> Task Exception (String, Dict)) -> 
  # (Request -> Task Exception (String, Dict)) ->     
  # String ->                                        
  # Request ->                                      
  # Task Exception Session
  
  def _session((skey,sess)):
    return Session(Cookie(ckey,skey), sess, [ SessionPut(k,sess[k]) for k in sess ])

  return to_maybe(getter(ckey, request)) >> (
    with_default( 
      creator(req).fmap(_session) , 
      lambda (skey,sess): resolve(Session(Cookie(ckey,skey), sess, [])) 
    )
  )


def put(key, val, (cookie, data, txs)):
  # String -> a -> Session -> Session
  if data.get(key) == val:
    return Session(cookie, data, txs)
  else:
    return Session(cookie, assoc(key,val,data), txs + [SessionPut(key,val)])

def remove(key, (cookie, data, txs)):
  # String -> Session -> Session
  return Session(cookie, dissoc(key,data), txs + [SessionRm(key)])

def clear((cookie, data, txs)):
  return Session(cookie, {}, txs + [SessionClear()])


def get(key, (cookie, data, txs)):
  return Just(data[key]) if data.has_key(key) else Nothing


def coalesce((cookie, data, txs)):
  # Session -> (Cookie, Dict)

  def _coalesce((c,d),tx):
    return match(SessionTx, {
      SessionPut: lambda k,v: (c, assoc(k,v,d))
      SessionRm: lambda k: (c, dissoc(k,d))
      SessionClear: always((c, {})) 
    }, tx)

  return reduce(_coalesce, txs, (cookie,{}))


