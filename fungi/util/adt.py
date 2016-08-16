"""
Simple ADTs and tagged-union matching in Python

Tip of the hat to [union-type](https://github.com/paldelpind/union-type), a
javascript library with similar aims and syntax.

Usage:

    Point = Type("Point", [int, int])
    Rectangle = Type("Rectangle", [Point, Point])
    Circle = Type("Circle", [int, Point])
    Triangle = Type("Triangle", [Point, Point, int])
    
    Shape = [ Rectangle, Circle, Triangle ]
    
    area = match(Shape, {
      Rectangle: (lambda (t,l), (b,r): (b - t) * (r - l)),
      Circle: (lambda r, (x,y): math.pi * (r**2)),
      Triangle: (lambda (x1,y1), (x2,y2), h: (((x2 - x1) + (y2 - y1)) * h)/2)
    })
    
    rect = Rectangle( Point(0,0), Point(100,100) )
    area(rect)  # => 10000
    
    circ = Circle( 5, Point(0,0) )
    area(circ)  # => 78.539816...
    
    tri = Triangle( Point(0,0), Point(100,100), 5 )
    area(tri)   # => 500
    
"""
from f import curry_n
 
def Type(tag, specs):
  class _tagged_tuple(tuple):
    def __eq__(self,other):
      return (
        self.__class__ == other.__class__ and 
        super(_tagged_tuple,self).__eq__(other)
      )
     
    # Note: only eval()-able if constructors are in scope with same name as tags     
    def __repr__(self):
      return (
        self.__class__.__name__ + 
        "( " + ", ".join(repr(p) for p in self) + " )"
      )

  _tagged_tuple.__name__ = tag
  
  @curry_n(len(specs))
  def _bind(*vals):    
    nvals = len(vals)
    nspecs = len(specs)
    if nvals > nspecs:
      raise TypeError, "Expected %d values, given %d" % (nspecs, nvals)
    
    for (i,(s,v)) in enumerate(zip(specs,vals)):
      ok, err = _validate(s,v)
      if not ok:
        msg = "Invalid type in field %d: %s" % (i,v)
        if not (err is None):
          msg = "%s\n  %s" % (msg, err)
        raise TypeError, msg
    
    return _tagged_tuple(vals)
    
  _bind.__name__ = "construct_%s" % tag
  _bind.__adt_class__ = _tagged_tuple
  return _bind


def typeof(adt):
  if not hasattr(adt, '__adt_class__'):
    raise TypeError, "Not an ADT constructor"
  return adt.__adt_class__

@curry_n(2)
def seqof(t,xs):
  return ( 
    hasattr(xs,'__iter__') and all( _validate(t,x)[0] for x in xs )
  )

def _validate(s,v):
  try:
    return ( isinstance(v,s), None )
  except TypeError:
    try:
      return (
        ( ( type(v) == s ) or
          ( hasattr(s,"__adt_class__") and isinstance(v,typeof(s)) ) or 
          ( callable(s) and s(v) == True )
        ), 
        None
      )
    except Exception as e:
      return (False, e)

 
@curry_n(3)  
def match(adts, cases, target):

  assert target.__class__ in [ typeof(adt) for adt in adts ],  \
    "%s is not in union" % target.__class__.__name__

  missing = [
    t.__adt_class__.__name__ for t in adts \
      if not (cases.has_key(type(None)) or cases.has_key(t))
  ]
  assert len(missing) == 0, \
    "No case found for the following type(s): %s" % ", ".join(missing)
  
  fn = None
  wildcard = False
  try:
    fn = ( 
      next( 
        cases[constr] for constr in cases \
          if isinstance(target,typeof(constr)) 
      )
    )

  except StopIteration:
    fn = cases.get(type(None),None)
    wildcard = not fn is None

  # note should never happen due to type assertions above
  if fn is None:
    raise TypeError("No cases match %s" % target.__class__.__name__)
  
  assert callable(fn), \
    "Matched case is not callable; check your cases"

  return fn() if wildcard else fn( *(slot for slot in target) )

