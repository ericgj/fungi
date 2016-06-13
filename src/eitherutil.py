from pymonad.Either import Left, Right
from taskmonad import Task

def with_default(default,either):
  if isinstance(either,Left):
    return default
  elif isinstance(either,Right):
    return either.value
  else:
    raise TypeError("Not an Either (Left or Right)")
    
def to_task(either):
  if isinstance(either,Left):
    return Task( lambda rej,_: rej(either.value) )
  elif isinstance(either,Right):
    return Task( lambda _,res: res(either.value) )
  else:
    raise TypeError("Not an Either (Left or Right)")

def fold(ifleft, ifright, either):
  if isinstance(either,Left):
    return ifleft(either.value)
  elif isinstance(either,Right):
    return ifright(either.value)
  else:
    raise TypeError("Not an Either (Left or Right)")

