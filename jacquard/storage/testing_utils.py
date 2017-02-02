# flake8: noqa

"""Misc utils for use in storage tests."""

import pytest
import hypothesis
import hypothesis.strategies

arbitrary_json = hypothesis.strategies.recursive(
    hypothesis.strategies.floats(allow_nan=False, allow_infinity=False) |
    hypothesis.strategies.booleans() |
    hypothesis.strategies.text() |
    hypothesis.strategies.none(),
    lambda children: (
        hypothesis.strategies.lists(children, average_size=2) |
        hypothesis.strategies.dictionaries(
            hypothesis.strategies.text(),
            children,
            average_size=1,
        )
    ),
    max_leaves=10,
).filter(lambda x: x is not None)
arbitrary_key = hypothesis.strategies.text(
    alphabet=hypothesis.strategies.characters(
        blacklist_categories=('whitespace',),
        blacklist_characters='*:\0',
    ),
).filter(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') == x)


class StorageGauntlet(object):
    """A standard gamut of tests run for any storage engine."""

    def setUp(self):
        super().setUp()
        self.setup_example()

    def setup_example(self):
        self.storage = self.open_storage()

    def open_storage(self):
        raise NotImplementedError()

    def test_smoke(self):
        with self.storage.transaction() as store:
            pass

    def test_smoke_read_only(self):
        with self.storage.transaction(read_only=True) as store:
            pass

    @hypothesis.given(key=arbitrary_key)
    def test_read_missing_key(self, key):
        with self.storage.transaction(read_only=True) as store:
            with pytest.raises(KeyError):
                store[key]

    @hypothesis.given(key=arbitrary_key, value=arbitrary_json)
    def test_read_after_write(self, key, value):
        with self.storage.transaction() as store:
            store[key] = value
        with self.storage.transaction(read_only=True) as store:
            assert store[key] == value

    @hypothesis.given(data=hypothesis.strategies.dictionaries(
        arbitrary_key,
        arbitrary_json,
        average_size=2,
    ))
    def test_enumerate_keys(self, data):
        with self.storage.transaction() as store:
            store.update(data)
        with self.storage.transaction(read_only=True) as store:
            assert set(store.keys()) == set(data.keys())

    @hypothesis.given(
        key=arbitrary_key,
        value1=arbitrary_json,
        value2=arbitrary_json,
    )
    def test_last_write_wins(self, key, value1, value2):
        with self.storage.transaction() as store:
            store[key] = value1
        with self.storage.transaction() as store:
            store[key] = value2
        with self.storage.transaction(read_only=True) as store:
            assert store[key] == value2

    @hypothesis.given(key=arbitrary_key, value=arbitrary_json)
    def test_deletions_remove_values(self, key, value):
        with self.storage.transaction() as store:
            store[key] = value
        with self.storage.transaction() as store:
            del store[key]
        with self.storage.transaction(read_only=True) as store:
            with pytest.raises(KeyError):
                store[key]

    @hypothesis.given(key=arbitrary_key, value=arbitrary_json)
    def test_deletions_remove_keys(self, key, value):
        with self.storage.transaction() as store:
            store[key] = value
        with self.storage.transaction() as store:
            del store[key]
        with self.storage.transaction(read_only=True) as store:
            assert list(store.keys()) == []
