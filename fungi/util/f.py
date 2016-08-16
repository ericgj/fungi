# functional toolbelt

from functools import partial, wraps, update_wrapper
from inspect import getargspec

def identity(x):
  return x

def always(x):
  return lambda *args: x

def fst((x,_)): 
  return x

def snd((_,x)): 
  return x

def flip(fn):
  def _fn(a,b,*args,**kwargs):
    return fn(b,a,*args,**kwargs)
  return curry(_fn)


"""
Derived from [fn.py](https://github.com/kachayev/fn.py) function 'curried'
Amended to fix wrapping error: cf. https://github.com/kachayev/fn.py/pull/75

Copyright 2013 Alexey Kachayev 
Under the Apache License, Version 2.0  
http://www.apache.org/licenses/LICENSE-2.0

"""
def curry(func):
  """A decorator that makes the function curried

  Usage example:

  >>> @curry
  ... def sum5(a, b, c, d, e):
  ...     return a + b + c + d + e
  ...
  >>> sum5(1)(2)(3)(4)(5)
  15
  >>> sum5(1, 2, 3)(4, 5)
  15
  """
  @wraps(func)
  def _curry(*args, **kwargs):
      f = func
      count = 0
      while isinstance(f, partial):
          if f.args:
              count += len(f.args)
          f = f.func

      spec = getargspec(f)

      if count == len(spec.args) - len(args):
          return func(*args, **kwargs)
          
      para_func = partial(func, *args, **kwargs)
      update_wrapper(para_func, f)
      return curry(para_func)
      
  return _curry


def curry_n(n):
  def _curry_n(func):
    @wraps(func)
    def _curry(*args, **kwargs):
      f = func
      
      count = 0
      while isinstance(f, partial) and count < n:
        if f.args:
          count += len(f.args)
        f = f.func

      if count >= n - len(args):
        return func(*args, **kwargs)
          
      para_func = partial(func, *args, **kwargs)
      update_wrapper(para_func, f)
      return _curry_n(para_func)
        
    return _curry
  
  return _curry_n
    
@curry
def applyf(args,fn):
  return fn(*args)

fapply = flip(applyf)

@curry
def tuple2(a,b):
  return (a,b)

def compose(*fs):
  if fs:
    pair = lambda f,g: lambda *a,**kw: f(g(*a,**kw))
    return reduce(pair, fs, identity)
  else:
    return identity

@curry
def fmap(f,it):
  return map(f,it) 

@curry
def merge(d2,d1):
  return dict( d1.items() + d2.items() )

@curry
def assoc(k,v,d):
  return merge({k:v},d)

@curry
def dissoc(k,d):
  return dict( [(k0,v) for (k0,v) in d.items() if not k == k0] )

@curry
def prop(k,d):
  return d.get(k)

def pick(ks,d):
  def _pick(acc,k):
    if d.has_key(k):
      acc[k] = d[k]
    return acc
  return reduce(_pick,ks,{})

@curry
def debug(msg,x):
  print "%s : %s" % (msg,str(x))
  return x



