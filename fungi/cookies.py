from webob.cookies import SignedCookieProfile, CookieProfile

from .util.f import always
from adt import Type, match

Cookie = Type('Cookie', [ unicode, always(True) ])  # key, value
SignedProfile = Type('SignedProfile', [dict, unicode, unicode])  # config, secret, salt
UnsignedProfile = Type('UnsignedProfile', [dict])  # config

Profile = [SignedProfile, UnsignedProfile]

# --- use these constructors instead of types directly

def signed_profile(secret, salt, config={}):
  return SignedProfile(config, secret, salt)

def unsigned_profile(config={}):
  return UnsignedProfile(config)

def cookie(name, value):
  return Cookie(name, value)


def adapter_for(name, profile):
  return match(Profile, {
    SignedProfile: (
      lambda config, secret, salt: SignedCookieProfile(secret, salt, name, **config)
    ),
    UnsignedProfile: (
      lambda config: CookieProfile(name, **config)
    )
  }, profile)

