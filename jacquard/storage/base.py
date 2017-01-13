"""Base class for storage engine implementations."""

import abc
import contextlib

from .utils import TransactionMap


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
