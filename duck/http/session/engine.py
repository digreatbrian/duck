"""
Module representing Duck default session engine, i.e. SessionStore class.
"""

import datetime
import uuid
import warnings
from typing import Optional

from duck.settings import SETTINGS
from duck.utils.importer import import_module_once

session_connector_mod = import_module_once(
    "duck.http.session.session_storage_connector")


class SessionError(Exception):
    """
    Session related errors.
    """


class SessionExpired(SessionError):
    """
    Raised on save operations if a session has already expired.
    """


class SessionStore(dict):
    """Session store for storing session data."""

    def __init__(self, session_key: str, disable_warnings: bool = False):
        """Initializes the session store."""
        super().__init__()
        self._session_key = session_key
        self._loaded = False
        self._modified = False
        self.disable_warnings = disable_warnings
        self.session_storage_connector = (
            session_connector_mod.get_session_storage_connector())

    @property
    def session_key(self):
        return self._session_key

    @session_key.setter
    def session_key(self, key: str):
        self._session_key = key

    @property
    def modified(self) -> bool:
        """Returns the state whether the session has been modified after load or creation."""
        return self._modified
    
    @modified.setter
    def modified(self, what: bool):
        """
        Sets whether the session has been modified.
        """
        self._modified = what
        
    def needs_update(self) -> bool:
        """
        Returns whether the session data is worthy to be saved, this is the lazy behavior of Duck.
        """
        if (self and self.session_key and self._modified
                and not ("expiry_date" in self and len(self) == 1)):
            # the session data is not empty, has been modified, session data length is (not 1 and containing only the key `expiry_date`)
            return True
        return False

    @staticmethod
    def generate_session_id() -> str:
        """Generates and returns a random session ID."""
        return str(uuid.uuid4())

    def get_expiry_age(self):
        """
        Returns the session max age from current settings.
        """
        return SETTINGS["SESSION_COOKIE_AGE"]

    def get_expiry_date(self):
        """
        Returns the datetime the session is going to expire.
        """
        expire_date = self.get("expiry_date")
        if not expire_date:
            self.set_expiry(datetime.datetime.utcnow() + datetime.timedelta(
                seconds=self.get_expiry_age()))
            return self.get_expiry_date()
        return expire_date

    def set_expiry(
        self,
        expiry: int | float | datetime.datetime | datetime.timedelta = None,
    ):
        """
        Sets the session expiry.

        Args:
                expiry (int | float | datetime.datetime | datetime.timedelta, optional): Float or int represents the seconds to expire from now and None represents the now plus the default session max_age.
        """
        if not expiry:
            self["expiry_date"] = datetime.datetime.utcnow(
            ) + datetime.timedelta(seconds=self.get_expiry_age())

        elif isinstance(expiry, (datetime.datetime, datetime.timedelta)):
            self["expiry_date"] = expiry

        elif isinstance(expiry, int, float):
            self["expiry_date"] = (datetime.datetime.utcnow()
                                   + datetime.timedelta(seconds=expiry))

        else:
            raise SessionError(
                f"Invalid expiry, expected any of [int, float, datetime.datetime, datetime.timedelta, None] but got '{type(expiry)}'"
            )

    @staticmethod
    def check_session_storage_connector(method):
        """Decorator to check if session storage is set and is correct"""
        from duck.http.session.session_storage_connector import SessionStorageConnector

        def wrapper(self, *a, **kw):

            def inner(*args, **kwargs):
                if not hasattr(self, "session_storage_connector"):
                    raise ValueError("Session storage connector is not set")

                if not self.session_storage_connector:
                    raise ValueError("Session storage connector is not set")

                assert isinstance(
                    self.session_storage_connector, SessionStorageConnector
                ), (f"Invalid session storage connector provided, should be an instance "
                    f"of {SessionStorageConnector} not {type(self.session_storage_connector)}"
                    )

                return method(self, *args, **kwargs)

            return inner(*a, **kw)

        return wrapper

    @check_session_storage_connector
    def load(self) -> dict:
        """
        Loads the session from storage.
        """
        if self._loaded and not self.disable_warnings:
            warnings.warn(
                f"{self.__class__.__name__} is already loaded; reloading may be inefficient."
            )
        session_data = (self.session_storage_connector.get_session(
            self.session_key) or {})
        self.update(session_data)
        if not self._loaded:
            self._modified = False # if session hasn't been loaded for the first time, set _modified to False
        self._loaded = True
        return session_data

    @check_session_storage_connector
    def save(self, *_):
        """Saves the session to storage."""
        if not self.session_key:
            raise ValueError("Session key is not set or invalid.")
        session_data = dict(self)
        expiry_date = self.get_expiry_date()
        now = datetime.datetime.utcnow()

        if now < expiry_date:
            # session not expired
            expiry_age = expiry_date - now
            expiry_age = expiry_age.total_seconds()
            self.session_storage_connector.set_session(self.session_key,
                                                       session_data,
                                                       expiry=expiry_age)
            self.session_storage_connector.save()
        else:
            raise SessionExpired(
                "Cannot save an expired session, use set_expiry to reset the session expiry."
            )
        self._modified = False  # reset session modification.

    @check_session_storage_connector
    def exists(self, session_key: str) -> bool:
        """Checks if a session with the specified key exists."""
        try:
            return bool(
                self.session_storage_connector.get_session(session_key))
        except KeyError:
            return False

    @check_session_storage_connector
    def create(self):
        """Creates a new session with a new session key."""
        self.session_key = self.generate_session_id()
        session_cookie_name = SETTINGS["SESSION_COOKIE_NAME"]

    @check_session_storage_connector
    def delete(self, session_key: Optional[str] = None):
        """Clears and deletes the session from session storage."""
        self.session_storage_connector.delete_session(session_key
                                                      or self.session_key)
        self.clear()

    def update(self, data: dict):
        """Overrides the update method to ensure items are tracked for modification."""
        super().update(data)
        if data:
            self._modified = True

    def clear(self):
        """Clears all session data."""
        is_empty = bool(self or None)
        super().clear()
        if not is_empty:
            self._modified = True

    def pop(self, *args, **kwargs):
        """Pops some session data."""
        data = super().pop(*args, **kwargs)
        self._modified = True
        return data

    def popitem(self, *args, **kwargs):
        """Pops some session data."""
        data = super().popitem(*args, **kwargs)
        self._modified = True
        return data

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._modified = True

    def __getitem__(self, key):
        value = super().__getitem__(key)

    def __delitem__(self, key):
        super().__delitem__(key)
        self._modified = True

    def __repr__(self):
        return f"<{self.__class__.__name__} {dict(self)}>"
