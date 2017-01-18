from jacquard.storage.redis import RedisStore

try:
    import fakeredis
except ImportError:
    fakeredis = None

import pytest
import functools
import unittest.mock


def redis_test(fn):
    @pytest.mark.skipif(
        fakeredis is None,
        reason="fakeredis is not installed",
    )
    @functools.wraps(fn)
    @unittest.mock.patch('redis.StrictRedis', fakeredis.FakeStrictRedis)
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        finally:
            fakeredis.FakeStrictRedis().flushall()

    return wrapper


@redis_test
def test_smoke():
    # Check no exceptions appear
    storage = RedisStore('')

    with storage.transaction() as store:
        pass


@redis_test
def test_get_nonexistent_key():
    # Just test this works without errors
    store = RedisStore('')
    assert store.get('test') is None


@redis_test
def test_simple_write():
    storage = RedisStore('')
    with storage.transaction() as store:
        store['test'] = "Bees"
    with storage.transaction() as store:
        assert store['test'] == "Bees"


@redis_test
def test_enumerate_keys():
    storage = RedisStore('')

    with storage.transaction() as store:
        store['foo1'] = "Bees"
        store['foo2'] = "Faces"

    with storage.transaction() as store:
        assert set(store.keys()) == set(('foo1', 'foo2'))


@redis_test
def test_update_key():
    storage = RedisStore('')

    with storage.transaction() as store:
        store['foo'] = "Bees"

    with storage.transaction() as store:
        store['foo'] = "Eyes"

    with storage.transaction() as store:
        assert store['foo'] == "Eyes"


@redis_test
def test_delete_key():
    storage = RedisStore('')

    with storage.transaction() as store:
        store['foo'] = "Bees"

    with storage.transaction() as store:
        del store['foo']

    with storage.transaction() as store:
        assert 'foo' not in store


@redis_test
def test_exceptions_back_out_writes():
    storage = RedisStore('')

    try:
        with storage.transaction() as store:
            store['foo'] = "Blah"
            raise RuntimeError()
    except RuntimeError:
        pass

    with storage.transaction() as store:
        assert 'foo' not in store
