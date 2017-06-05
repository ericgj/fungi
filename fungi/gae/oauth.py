import logging
from google.appengine.ext import ndb
from oauth2client.client import Credentials

from pymonad.Maybe import Nothing, Just
import pymonad_extra.util.task as task

from fungi.util.err import reject_errors

log = logging.getLogger(__name__)

def CredentialsStore():
  return Store(CredentialsNDBModel, 'credentials')

class Store(object):
 
  def __init__(self,model,prop):
    self._model = model
    self._prop = prop

  def get(self,uid):
    @reject_errors
    def _get():
      ent = self._model.get_by_id(uid)
      if ent is None:
        return Nothing
      else:
        prop = None
        try:
          prop = getattr(ent,self._prop)
          return Just(prop)
        except AttributeError:
          return Nothing
    return _get()

  def put(self,uid,val):
    @reject_errors
    def _put():
      ent = self._model.get_or_insert(uid)
      setattr(ent, self._prop, val)
      return ent.put()
    return _put()

  def delete(self,uid):
    @reject_errors
    def _delete():
      key = ndb.Key(self._model, uid)
      return key.delete()
    return _delete()

  def delete_all(self):
    def _delete(key):
      @reject_errors
      def _delete_task():
        return key.delete()
      return _delete_task()

    return task.sequence([
      _delete(key) for key in self._model.query().iter(keys_only=True)
    ])
  


# Copied from oauth2client.contrib._appengine_ndb


# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google App Engine utilities helper.

Classes that directly require App Engine's ndb library. Provided
as a separate module in case of failure to import ndb while
other App Engine libraries are present.
"""


NDB_KEY = ndb.Key
"""Key constant used by :mod:`oauth2client.contrib.appengine`."""

NDB_MODEL = ndb.Model
"""Model constant used by :mod:`oauth2client.contrib.appengine`."""


class CredentialsNDBProperty(ndb.BlobProperty):
    """App Engine NDB datastore Property for Credentials.

    Serves the same purpose as the DB CredentialsProperty, but for NDB
    models. Since CredentialsProperty stores data as a blob and this
    inherits from BlobProperty, the data in the datastore will be the same
    as in the DB case.

    Utility property that allows easy storage and retrieval of Credentials
    and subclasses.
    """

    def _validate(self, value):
        """Validates a value as a proper credentials object.

        Args:
            value: A value to be set on the property.

        Raises:
            TypeError if the value is not an instance of Credentials.
        """
        log.debug('validate: Got type %s', type(value))
        if value is not None and not isinstance(value, Credentials):
            raise TypeError('Property %s must be convertible to a '
                            'credentials instance; received: %s.' %
                            (self._name, value))

    def _to_base_type(self, value):
        """Converts our validated value to a JSON serialized string.

        Args:
            value: A value to be set in the datastore.

        Returns:
            A JSON serialized version of the credential, else '' if value
            is None.
        """
        if value is None:
            return ''
        else:
            return value.to_json()

    def _from_base_type(self, value):
        """Converts our stored JSON string back to the desired type.

        Args:
            value: A value from the datastore to be converted to the
                   desired type.

        Returns:
            A deserialized Credentials (or subclass) object, else None if
            the value can't be parsed.
        """
        if not value:
            return None
        try:
            # Uses the from_json method of the implied class of value
            credentials = Credentials.new_from_json(value)
        except ValueError:
            credentials = None
        return credentials


class CredentialsNDBModel(ndb.Model):
    """NDB Model for storage of OAuth 2.0 Credentials

    Since this model uses the same kind as CredentialsModel and has a
    property which can serialize and deserialize Credentials correctly, it
    can be used interchangeably with a CredentialsModel to access, insert
    and delete the same entities. This simply provides an NDB model for
    interacting with the same data the DB model interacts with.

    Storage of the model is keyed by the user.user_id().
    """
    credentials = CredentialsNDBProperty()

    @classmethod
    def _get_kind(cls):
        """Return the kind name for this class."""
        return 'CredentialsModel'

