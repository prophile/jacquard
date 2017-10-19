import pytest
import unittest

from jacquard.storage.dummy import DummyStore
from jacquard.storage.testing_utils import StorageGauntlet


class DummyGauntletTest(StorageGauntlet, unittest.TestCase):
    def open_storage(self):
        return DummyStore('')

    def test_transaction_raises_error_for_bad_commit(self):
        store = self.open_storage()
        transaction = store.transaction(read_only=True)
        transaction_map = transaction.__enter__()

        transaction_map['new_key'] = 'new_value'

        with pytest.raises(RuntimeError):
            transaction.__exit__(None, None, None)

        assert 'new_key' not in store.data
