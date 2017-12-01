"""Dummy, in-memory storage engine."""

import json
import threading

from jacquard.storage.base import StorageEngine


class DummyStore(StorageEngine):
    """Dummy, in-memory storage engine."""

    def __init__(self, connection_string, *, data=None):
        """
        Make it so.

        The connection string is ignored. If the magic keyword argument `data`
        is provided it is used for the initial data - very handy for unit
        tests!
        """
        if data is not None:
            self.data = {
                key: json.dumps(value)
                for key, value in data.items()
            }
        else:
            self.data = {}
        self.lock = threading.Lock()

    def __getitem__(self, key):
        """Direct item access. This is for test usage."""
        return json.loads(self.data.get(key, 'null'))

    def begin(self):
        """Begin transaction."""
        self.lock.acquire()

    def commit(self, changes, deletions):
        """Commit transaction."""
        self.data.update(changes)
        for deletion in deletions:
            del self.data[deletion]
        self.lock.release()

    def rollback(self):
        """Roll back transaction."""
        self.lock.release()

    def keys(self):
        """All keys."""
        return self.data.keys()

    def get(self, key):
        """Get value."""
        return self.data.get(key)
