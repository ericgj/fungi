import json
from pymonad.Either import Left, Right
from .f import curry
from . import err

@curry
def encode_with_options(opts,encoder,data):
  # Dict -> JSONEncoder -> a -> Either Exception String

  r = None
  try:
    r = json.dumps(data, cls=encoder, **opts)
    return Right(r)

  except Exception as e:
    return Left(err.wrap(e))

encode_with = encode_with_options({'separators': (',',':')})
encode = encode_with(json.JSONEncoder)
pretty_encode = encode_with_options({'indent': 2}, json.JSONEncoder)

@curry
def decode_with_options(opts,decoder,s):
  # Dict -> JSONDecoder -> String -> Either Exception a

  r = None
  try:
    r = json.loads(s, cls=decoder, **opts)
    return Right(r)

  except Exception as e:
    return Left(err.wrap(e))

decode_with = decode_with_options({})
decode = decode_with(json.JSONDecoder)

