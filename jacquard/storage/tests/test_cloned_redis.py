import functools
import unittest.mock

import pytest

from jacquard.storage.exceptions import Retry
from jacquard.storage.cloned_redis import ClonedRedisStore, destroy_shared_data

try:
    import fakeredis
except ImportError:
    fakeredis = None



def cloned_redis_test(fn):
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
            destroy_shared_data()

    return wrapper


@cloned_redis_test
def test_smoke():
    # Check no exceptions appear
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        pass


@cloned_redis_test
def test_get_nonexistent_key():
    # Just test this works without errors
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        assert store.get('test') is None


@cloned_redis_test
def test_simple_write():
    storage = ClonedRedisStore('')
    with storage.transaction() as store:
        store['test'] = "Bees"
    with storage.transaction() as store:
        assert store['test'] == "Bees"


@cloned_redis_test
def test_enumerate_keys():
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        store['foo1'] = "Bees"
        store['foo2'] = "Faces"

    with storage.transaction() as store:
        assert set(store.keys()) == {'foo1', 'foo2'}


@cloned_redis_test
def test_update_key():
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        store['foo'] = "Bees"

    with storage.transaction() as store:
        store['foo'] = "Eyes"

    with storage.transaction() as store:
        assert store['foo'] == "Eyes"


@cloned_redis_test
def test_delete_key():
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        store['foo'] = "Bees"

    with storage.transaction() as store:
        del store['foo']

    with storage.transaction() as store:
        assert 'foo' not in store


@cloned_redis_test
def test_exceptions_back_out_writes():
    storage = ClonedRedisStore('')

    try:
        with storage.transaction() as store:
            store['foo'] = "Blah"
            raise RuntimeError()
    except RuntimeError:
        pass

    with storage.transaction() as store:
        assert 'foo' not in store


@cloned_redis_test
def test_raises_retry_on_concurrent_write():
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        store['foo'] = "Bar"

    with pytest.raises(Retry):
        with storage.transaction() as store:
            fakeredis.FakeStrictRedis().set(b'jacquard-store:state-key', b'different')
            store['foo'] = "Bazz"
