"""General storage engine utilities."""

import json
import logging
import functools
import collections.abc

from jacquard.plugin import plug

from .exceptions import Retry


def retrying(fn):
    """Decorator: reissues the function if it raises Retry."""
    logger = logging.getLogger('jacquard.storage.retrying')

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        while True:
            try:
                return fn(*args, **kwargs)
            except Retry:
                callable_name = getattr(fn, '__name__', 'anonymous function')
                logger.debug("Retry issued from %s, reissuing", callable_name)

    return wrapper


def copy_data(from_engine, to_engine, flush=False):
    """Copy all keys between two storage engines."""
    with from_engine.transaction(read_only=True) as src:
        with to_engine.transaction() as dst:
            if flush:
                dst.clear()
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
        current_keys = {
            x
            for x in self._store_keys
            if x not in self.deletions
        }
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
            return self._cache[key]
        except KeyError:
            result = self.store.get(self.store.encode_key(key))

        if result is None:
            self._cache[key] = None
            raise KeyError(key)

        # UTF-8 decoding
        if isinstance(result, bytes):
            result = result.decode('utf-8')

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
        old_value = self.get(key)
        if old_value is None:
            raise KeyError(key)

        self._cache[key] = None
        encoded_key = self.store.encode_key(key)
        try:
            del self.changes[encoded_key]
        except KeyError:
            pass
        self.deletions.add(encoded_key)


def open_engine(config, engine, url):
    """
    Open and connect to a given engine and URL.

    This looks up the backend through the entry points mechanism, and is
    pluggable by adding `StorageEngine` subclasses to the entry points
    group `jacquard.storage_engines`.
    """
    cls = plug('storage_engines', engine, config=config)()
    return cls(url)
