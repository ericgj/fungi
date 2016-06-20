
from f import curry
from pymonad.Maybe import Nothing, Just
from pymonad_extra import Task

@curry
def with_default(val,maybe):
  if isinstance(maybe,Just): 
    return maybe.getValue() 
  elif maybe == Nothing:
    return val
  else:
    raise TypeError("Not a Maybe")

@curry
def to_task(e,maybe):
  return with_default(
    Task( lambda rej,_: rej(e) ),
    maybe.fmap( lambda x: Task( lambda _,res: res(x) ) )
  )

