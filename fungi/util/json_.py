import json
from pymonad.Either import Left, Right
from f import curry
import err

@curry
def encode_with(encoder,data):
  # JSONEncoder -> a -> Either Exception String

  r = None
  try:
    r = json.dumps(data, cls=encoder, separators=(',',':'))
    return Right(r)

  except Exception as e:
    return Left(err.wrap(e))

encode = encode_with(json.JSONEncoder)

@curry
def decode_with(decoder,s):
  # JSONDecoder -> String -> Either Exception a

  r = None
  try:
    r = json.loads(s, cls=decoder)
    return Right(r)

  except Exception as e:
    return Left(err.wrap(e))

decode = decode_with(json.JSONDecoder)

