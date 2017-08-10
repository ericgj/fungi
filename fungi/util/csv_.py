import unicodecsv

from ..util.f import curry
from ..util.err import reject_errors

@curry
def write_tuples(encoding, fields, iter, f):
  return write_tuples_with_options({}, encoding, fields, iter, f)

@curry
def write_dicts(encoding, fields, iter, f):
  return write_dicts_with_options({}, encoding, fields, iter, f)

@curry
def write_tsv_tuples(encoding, fields, iter, f):
  return write_tuples_with_options({'dialect': 'excel-tab'}, encoding, fields, iter, f)

@curry
def write_tsv_dicts(encoding, fields, iter, f):
  return write_dicts_with_options({'dialect': 'excel-tab'}, encoding, fields, iter, f)


@curry
def write_tuples_with_options(opts, encoding, fields, iter, f):
  # Dict -> String -> List String -> Iterable tuple -> Stream -> Task Exception Stream
  @reject_errors
  def _write():
    w = unicodecsv.writer(f, encoding=encoding, **opts)
    w.writerow(fields)
    for r in iter:
      w.writerow(r)
    return f
  return _write()

@curry
def write_dicts_with_options(opts, encoding, fields, iter, f):
  # String -> List String -> Iterable Dict -> Stream -> Task Exception Stream
  @reject_errors
  def _write():
    w = unicodecsv.DictWriter(f, fieldnames=fields, encoding=encoding, **opts)
    w.writeheader()
    for r in iter:
      w.writerow(r)
    return f
  return _write()

