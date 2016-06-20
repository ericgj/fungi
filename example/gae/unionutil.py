
from f import curry

@curry
def match(uniontype,cases,target):
  assert issubclass(target.__class__,uniontype), \
    "%s is not in union type" % target.__class__.__name__

  utypes = []
  if hasattr(uniontype,'__union_set_params__'):
    utypes = uniontype.__union_set_params__
  else:
    utypes = [uniontype]   # in case where union type is flattened to single type

  missing = [
    t.__name__ for t in utypes \
      if not (cases.has_key(type(None)) or cases.has_key(t))
  ]
  assert len(missing) == 0, \
    "No case found for the following type(s): %s" % ", ".join(missing)

  fn = None
  wildcard = False
  try:
    fn = ( 
      next( cases[klass] for klass in cases if isinstance(target,klass) )
    )

  except StopIteration:
    fn = cases.get(type(None),None)
    wildcard = bool(fn)

  # note should never happen due to type assertions above
  if fn is None:
    raise TypeError("No cases match %s" % target.__class__.__name__)
  
  assert callable(fn), \
    "Matched case is not callable; check your cases"

  return fn() if wildcard else fn( *(slot for slot in target) )


