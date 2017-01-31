"""Base class for storage engine implementations."""

import abc
import contextlib

from .utils import TransactionMap


class StorageEngine(metaclass=abc.ABCMeta):
    """
    Base storage engine class.

    StorageEngine subclasses are not under any obligation to be thread-safe.
    """

    @abc.abstractmethod
    def __init__(self, connection_string):
        """
        Construct with a given connection string.

        It is typical for the connection string to be a URL: even for files it
        should generally take the form of a file: scheme URL.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def begin(self):
        """Enter a new transaction."""
        raise NotImplementedError

    def begin_read_only(self):
        """
        Enter a new, read-only transaction.

        May be overloaded for efficiency - by default, just calls begin().
        """
        self.begin()

    @abc.abstractmethod
    def commit(self, changes, deletions):
        """
        Commit transaction.

        Writes to make are given in the two arguments: `changes` is a mapping
        of keys to their new string values, and `deletions` is an iterable of
        keys to remove entirely.

        If optimistic locking or other transactional mechanisms fail, this can
        raise the `Retry` exception to request that the entire transaction be
        repeated.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        """
        Roll back the current transaction without writing any changes.

        This is used not only in exceptions but also when no writes were
        necessary after a transaction, so should ideally be fairly fast.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def keys(self):
        """
        Get an iterable over all keys in the store.

        This is only ever called in transactions.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, key):
        """
        Get the current value corresponding with a given key.

        Where there is no current value this must return `None`.

        Only ever called in a transaction.
        """
        raise NotImplementedError

    def encode_key(self, key):
        """
        Convert a given key for use in the storage engine.

        This optional method is given for engine-specific encodings of keys -
        for instance, replacing slashes with the more idiomatic colons and
        prefix for the Redis backend. All keys entering the rest of the API
        are encoded.

        The default implementation is the identity function.
        """
        return key

    def decode_key(self, key):
        """
        Convert a given key for use in Jacquard.

        This optional method must be implemented if `encode_key` is given,
        and must be its inverse.

        The default implementation is the identity function.
        """
        return key

    @contextlib.contextmanager
    def transaction(self, read_only=False):
        """
        Run a transactional sequence on this store.

        This is (currently?) the main user API for `StorageEngine`. The
        context manager yields an object supporting the mutable mapping
        protocol in all its glory, which can be treated as if a dict in,
        say, the standard library's `shelve` module.

        When the context manager exits, the transaction is rolled back if
        there are no writes or if an exception is escaping.

        Commits are allowed to raise the `Retry` exception and it is left to
        users of the API to deal with this. `Retry` is guaranteed not to be
        raised if the transaction was read-only.
        """
        if read_only:
            self.begin_read_only()
        else:
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
        elif (
            transaction_map.changes or
            transaction_map.deletions
        ) and read_only:
            self.rollback()
            raise RuntimeError(
                "Commit in read-only transaction (keys: %s)" %
                ', '.join(
                    repr(x)
                    for x in (
                        set(transaction_map.changes.keys()) |
                        set(transaction_map.deletions)
                    )
                )
            )
        else:
            self.commit(
                transaction_map.changes,
                transaction_map.deletions,
            )
