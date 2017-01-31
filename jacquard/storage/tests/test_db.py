from jacquard.storage.db import DBStore


def test_get_nonexistent_key():
    # Just test this works without errors
    store = DBStore('sqlite://')
    assert store.get('test') is None


def test_simple_write():
    storage = DBStore('sqlite://')
    with storage.transaction() as store:
        store['test'] = "Bees"
    with storage.transaction() as store:
        assert store['test'] == "Bees"


def test_enumerate_keys():
    storage = DBStore('sqlite://')

    with storage.transaction() as store:
        store['foo1'] = "Bees"
        store['foo2'] = "Faces"

    with storage.transaction() as store:
        assert set(store.keys()) == set(('foo1', 'foo2'))


def test_update_key():
    storage = DBStore('sqlite://')

    with storage.transaction() as store:
        store['foo'] = "Bees"

    with storage.transaction() as store:
        store['foo'] = "Eyes"

    with storage.transaction(read_only=True) as store:
        assert store['foo'] == "Eyes"


def test_delete_key():
    storage = DBStore('sqlite://')

    with storage.transaction() as store:
        store['foo'] = "Bees"

    with storage.transaction() as store:
        del store['foo']

    with storage.transaction() as store:
        assert 'foo' not in store


def test_deleted_keys_do_not_appear_in_keys_call():
    storage = DBStore('sqlite://')

    with storage.transaction() as store:
        store['foo'] = "Bees"

    with storage.transaction() as store:
        del store['foo']

    with storage.transaction() as store:
        assert 'foo' not in list(store.keys())


def test_exceptions_back_out_writes():
    storage = DBStore('sqlite://')

    try:
        with storage.transaction() as store:
            store['foo'] = "Blah"
            raise RuntimeError()
    except RuntimeError:
        pass

    with storage.transaction() as store:
        assert 'foo' not in store
