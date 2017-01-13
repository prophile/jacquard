import collections.abc
import json


def copy_data(from_engine, to_engine):
    with from_engine.transaction() as src:
        with to_engine.transaction() as dst:
            dst.update(src)


class TransactionMap(collections.abc.MutableMapping):
    def __init__(self, store):
        self.store = store
        self._store_keys = None
        self.changes = {}
        self.deletions = set()
        self._cache = {}

    def _get_keys(self):
        if self._store_keys is None:
            self._store_keys = list(self.store.keys())
        current_keys = set(
            x
            for x in self._store_keys
            if x not in self.deletions
        )
        current_keys.update(self.changes.keys())
        return sorted(
            self.store.decode_key(x) for x in current_keys
        )

    def __len__(self):
        return len(self._get_keys())

    def __iter__(self):
        return iter(self._get_keys())

    def __getitem__(self, key):
        try:
            result = self._cache[key]
        except KeyError:
            result = self.store.get(self.store.encode_key(key))

        if result is None:
            self._cache[key] = None
            raise KeyError(key)

        result = json.loads(result)

        self._cache[key] = result

        return result

    def __setitem__(self, key, value):
        self._cache[key] = value
        encoded_key = self.store.encode_key(key)
        self.changes[encoded_key] = json.dumps(value)
        self.deletions.discard(encoded_key)

    def __delitem__(self, key):
        self._cache[key] = None
        encoded_key = self.store.encode_key(key)
        try:
            del self.changes[encoded_key]
        except KeyError:
            pass
        self.deletions.add(encoded_key)
