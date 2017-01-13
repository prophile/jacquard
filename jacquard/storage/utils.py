"""General storage engine utilities."""

import collections.abc
import json

import pkg_resources


def copy_data(from_engine, to_engine):
    """Copy all keys between two storage engines."""
    with from_engine.transaction() as src:
        with to_engine.transaction() as dst:
            dst.update(src)


class TransactionMap(collections.abc.MutableMapping):
    """
    Mutable mapping built on storage engines.

    Data are fetched through `.get` and `.keys` on `StorageEngine`, but changes
    are kept in the `changes` and `deletions` attributes which correspond with
    the two arguments of the same name to `.commit`.
    """

    def __init__(self, store):
        """Initialise from storage engine."""
        self.store = store
        self._store_keys = None
        self.changes = {}
        self.deletions = set()
        self._cache = {}

    def _get_keys(self):
        """Get all (decoded) keys from storage engine."""
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
        """Number of keys."""
        return len(self._get_keys())

    def __iter__(self):
        """Iterator over keys."""
        return iter(self._get_keys())

    def __getitem__(self, key):
        """Lookup by key. Respects any pending changes/deletions."""
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
        """Overwrite or set key."""
        self._cache[key] = value
        encoded_key = self.store.encode_key(key)
        self.changes[encoded_key] = json.dumps(value)
        self.deletions.discard(encoded_key)

    def __delitem__(self, key):
        """Delete key."""
        self._cache[key] = None
        encoded_key = self.store.encode_key(key)
        try:
            del self.changes[encoded_key]
        except KeyError:
            pass
        self.deletions.add(encoded_key)


def open_engine(engine, url):
    """
    Open and connect to a given engine and URL.

    This looks up the backend through the entry points mechanism, and is
    pluggable by adding `StorageEngine` subclasses to the entry points
    group `jacquard.storage_engines`.
    """
    entry_point = None

    for candidate_entry_point in pkg_resources.iter_entry_points(
        'jacquard.storage_engines',
        name=engine,
    ):
        entry_point = candidate_entry_point

    if entry_point is None:
        raise RuntimeError("Cannot find storage engine '%s'" % engine)

    cls = entry_point.load()
    return cls(url)
