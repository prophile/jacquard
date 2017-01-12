import json

from .base import KVStore


class DummyStore(KVStore):
    def __init__(self, connection_string, *, data=None):
        if data is not None:
            self.data = {
                key: json.dumps(value)
                for key, value in data.items()
            }
        else:
            self.data = {}

    def begin(self):
        pass

    def commit(self, changes, deletions):
        self.data.update(changes)
        for deletion in deletions:
            del self.data[deletion]

    def rollback(self):
        pass

    def keys(self):
        return self.data.keys()

    def get(self, key):
        return self.data.get(key)
