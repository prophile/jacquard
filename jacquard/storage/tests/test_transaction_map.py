import pytest

from jacquard.storage.dummy import DummyStore
from jacquard.storage.utils import TransactionMap


def test_duplicate_accesses_continue_to_raise_keyerror():
    store = DummyStore("")
    transaction_map = TransactionMap(store)

    with pytest.raises(KeyError):
        transaction_map["test"]

    with pytest.raises(KeyError):
        transaction_map["test"]
