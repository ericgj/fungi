from pymonad.Monoid import Monoid, mconcat

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

class Batch(Op):
  def __str__(self):
    return ", ".join([ str(op) for op in self.value ])

# --- Op constructors

def no_op():
  return NoOp(())

def set_cookie(cookie):
  return SetCookie(cookie)

def gzip():
  return Gzip(())

def set_etag():
  return SetETag(())

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
  elif isinstance(op, Batch):
    for o in op.value:
      finalize(o, resp)
  return resp


def exec_set_cookie(cookie, resp):
  resp.set_cookie(cookie)

def exec_gzip(resp):
  resp.encode_content(encoding='gzip')

def exec_set_etag(resp):
  resp.md5_etag()


