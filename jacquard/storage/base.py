import abc
import json
import contextlib
import collections.abc


class Retry(Exception):
    pass


class KVStore(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, connection_string):
        pass

    @abc.abstractmethod
    def begin(self):
        pass

    @abc.abstractmethod
    def commit(self, changes, deletions):
        pass

    @abc.abstractmethod
    def rollback(self):
        pass

    @abc.abstractmethod
    def keys(self):
        pass

    @abc.abstractmethod
    def get(self, key):
        pass

    def encode_key(self, key):
        return key

    def decode_key(self, key):
        return key

    @contextlib.contextmanager
    def transaction(self):
        self.begin()

        transaction_map = TransactionMap(self)

        try:
            yield transaction_map
        except Exception:
            self.rollback()
            raise

        if (
            not transaction_map.changes and
            not transaction_map.deletions
        ):
            # Don't bother running a commit if nothing actually changed
            self.rollback()
        else:
            self.commit(
                transaction_map.changes,
                transaction_map.deletions,
            )


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
