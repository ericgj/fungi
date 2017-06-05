from webob.cookies import SignedCookieProfile, CookieProfile

from util.f import curry, always
import util.err as err
from adt import Type, match

Cookie = Type('Cookie', [ unicode, always(True) ])  # key, value
SignedProfile = Type('SignedProfile', [dict, unicode, unicode])  # config, secret, salt
UnsignedProfile = Type('UnsignedProfile', [dict])  # config

Profile = [SignedProfile, UnsignedProfile]

@curry
def get(profile, name, req):
  # Profile -> String -> Request -> Task Exception a

  def _get(rej,res):
    adapter = _adapter_for(name, profile).bind(req)
    try:
      res(adapter.get_value())
    except Exception as e:
      rej(err.wrap(e))

  return Task(_get)

@curry
def put(profile, (name, val), resp):
  # Profile -> Cookie -> Response -> Task Exception Response

  def _put(rej,res):
    adapter = _adapter_for(name, profile)
    try:
      adapter.set_cookies(resp, val)
      res(resp)
    except Exception as e:
      rej(err.wrap(e))

  return Task(_put)

def writer(profile):
  # Profile -> (Cookie -> Response -> Task Exception Response)
  # convenience function
  return put(profile)


def _adapter_for(name, profile):
  return match(Profile, {
    SignedProfile: (
      lambda config, secret, salt: SignedCookieProfile(secret, salt, name, **config)
    ),
    UnsignedProfile: (
      lambda config: CookieProfile(name, **config)
    )
  }, profile)

