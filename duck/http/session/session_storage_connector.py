"""
Module containing SessionConnector class which can be used to connect to
session storage to perform operations like get, set, update, delete, clear, etc.
"""

import os
import uuid
from typing import Callable

from duck.settings import SETTINGS
from duck.settings.loaded import SESSION_STORAGE
from duck.utils.caching import CacheBase, InMemoryCache
from duck.utils.importer import import_module_once

globals = import_module_once("duck.globals")


def get_session_storage_connector():
    """Returns the session storage connector object"""

    if not globals.session_storage_connector:
        session_storage_cls = SESSION_STORAGE
        globals.session_storage_connector = SessionStorageConnector(
            session_storage_cls)
    return globals.session_storage_connector


class NonPersistentStorageError(Exception):
    pass


class SessionStorageConnector:
    """
    This class is used to connect to the session storage and perform almost all the operations on the session storage
    """

    def __init__(self, session_storage_cls: Callable):
        """
        Initialize SessionStorageConnector

        Args:
                session_storage_cls (Callable): Class to initialize the session storage object
        """
        self.session_dir = SETTINGS["SESSION_DIR"]
        self.session_storage_cls = session_storage_cls

        if self.session_dir:
            os.makedirs(self.session_dir, exist_ok=True)

        try:
            self._session_storage = session_storage_cls()
        except TypeError:
            self._session_storage = session_storage_cls(self.session_dir)

    @staticmethod
    def generate_session_id() -> str:
        """Retrieve a random generated session ID"""
        return str(uuid.uuid4())

    def set_session(self,
                    session_id: str,
                    data: dict,
                    expiry: int | float = None):
        """Set session data"""
        if expiry:
            self._session_storage.set(session_id, data, expiry)
        else:
            self._session_storage.set(session_id, data)

    def update_session(self, session_id, data: dict):
        """Update the session data"""
        prev_data = self.get_session(session_id) or {}
        prev_data.update(data)
        self.set_session(session_id, prev_data)

    def get_session(self, session_id: str):
        """Get session data"""
        return self._session_storage.get(session_id)

    def delete_session(self, session_id: str):
        """Delete session data"""
        self._session_storage.delete(session_id)

    def clear_all_sessions(self):
        """Clear all session data"""
        self._session_storage.clear()

    def save(self):
        """Saves the current sessions to session storage"""
        self._session_storage.save()

    def close(self):
        """Close the session storage"""
        self._session_storage.close()

    def __new__(cls, session_storage_cls: CacheBase):
        from duck.meta import Meta

        if not Meta.get_metadata("SESSION_STORAGE_SET"):
            Meta.set_metadata("SESSION_STORAGE_SET", True)
        else:
            if issubclass(session_storage_cls, InMemoryCache):
                raise NonPersistenceStorageError(
                    "SessionStorageConnector should only be instantiated once. Multiple instances may lead to data inconsistency, "
                    "corruption, or loss. Ensure that the SessionStorageConnector is created only once throughout the application lifecycle."
                )
        return super().__new__(cls)
