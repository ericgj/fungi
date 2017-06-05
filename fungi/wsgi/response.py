from pymonad.Monoid import Monoid, mconcat

from util.f import curry
import cookies

# --- Note: do not instanciate directly, use constructors below

class Op(Monoid):
  
  @staticmethod
  def mzero():
    return NoOp()

  def __str__(self):
    return self.__class__.__name__

  def mplus(self,other):
    if isinstance(self, Batch):
      if isinstance(other, Batch):
        return Batch(self.value + other.value)
      else:
        if isinstance(other, NoOp):
          return self
        else:
          return Batch(self.value + [other])
    else:
      if isinstance(other, Batch):
        if isinstance(self, NoOp):
          return other
        else:
          return Batch([self] + other.value)
      else:
        if isinstance(self, NoOp):
          return other
        else:
          if isinstance(other, NoOp):
            return self
          else:
            return Batch([self, other])

class NoOp(Op):
  pass

class SetCookie(Op):
  pass

class Gzip(Op):
  pass

class SetETag(Op):
  pass

class CacheControl(Op):
  pass

class CacheExpires(Op):
  pass

class Batch(Op):
  def __str__(self):
    return ", ".join([ str(op) for op in self.value ])


# --- Op constructors

def no_op():
  return NoOp(())

@curry
def set_cookie(profile,cookie):
  return SetCookie((profile,cookie))

def gzip():
  return Gzip(())

def set_etag():
  return SetETag(())

def cache_control(opts):
  return CacheControl(opts)

def cache_expires(secs):
  return CacheExpires(secs)

def batch_ops(ops):
  return mconcat(ops)


# --- Mutation below

def finalize(op, resp):
  if isinstance(op, NoOp):
    pass
  elif isinstance(op, SetCookie):
    exec_set_cookie(op.value, resp)
  elif isinstance(op, Gzip):
    exec_gzip(resp)
  elif isinstance(op, SetETag):
    exec_set_etag(resp)
  elif isinstance(op, CacheControl):
    exec_cache_control(op.value, resp)
  elif isinstance(op, CacheExpires):
    exec_cache_expires(op.value, resp)
  elif isinstance(op, Batch):
    for o in op.value:
      finalize(o, resp)
  return resp


def exec_set_cookie((profile,(name,value)), resp):
  cookies.adapter_for(name,profile).set_cookies(resp, value)

def exec_gzip(resp):
  resp.encode_content(encoding='gzip')

def exec_set_etag(resp):
  resp.md5_etag()

def exec_cache_control(opts,resp):
  resp.cache_control = opts

def exec_cache_expires(secs,resp):
  resp.cache_expires = secs

