import functools
import unittest.mock

import pytest
import hypothesis
import hypothesis.strategies

from jacquard.storage.exceptions import Retry
from jacquard.storage.cloned_redis import ClonedRedisStore, resync_all_connections

try:
    import fakeredis
except ImportError:
    fakeredis = None


arbitrary_key = hypothesis.strategies.characters()
arbitrary_json = hypothesis.strategies.recursive(
    hypothesis.strategies.floats(allow_nan=False, allow_infinity=False) |
    hypothesis.strategies.booleans() |
    hypothesis.strategies.text() |
    hypothesis.strategies.none(),
    lambda children: (
        hypothesis.strategies.lists(children) |
        hypothesis.strategies.dictionaries(
            hypothesis.strategies.text(),
            children,
        )
    ),
).filter(lambda x: x is not None)


def cloned_redis_test(**kwargs):
    def decorator(fn):
        @functools.wraps(fn)
        @unittest.mock.patch('redis.StrictRedis', fakeredis.FakeStrictRedis)
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            finally:
                fakeredis.FakeStrictRedis().flushall()
                resync_all_connections()

        if kwargs:
            wrapper = hypothesis.given(**kwargs)(wrapper)

        wrapper = pytest.mark.skipif(
            fakeredis is None,
            reason="fakeredis is not installed",
        )(wrapper)

        return wrapper
    return decorator


@cloned_redis_test()
def test_smoke():
    # Check no exceptions appear
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        pass


@cloned_redis_test(
    key=arbitrary_key,
)
def test_get_nonexistent_key(key):
    # Just test this works without errors
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        assert store.get(key) is None


@cloned_redis_test(
    key=arbitrary_key,
    value=arbitrary_json,
)
def test_simple_write(key, value):
    storage = ClonedRedisStore('')
    with storage.transaction() as store:
        store[key] = value
    with storage.transaction() as store:
        assert store[key] == value

@cloned_redis_test(
    values=hypothesis.strategies.dictionaries(
        arbitrary_key,
        arbitrary_json,
    ),
)
def test_enumerate_keys(values):
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        store.update(values)

    with storage.transaction(read_only=True) as store:
        assert set(store.keys()) == set(values.keys())


@cloned_redis_test(
    key=arbitrary_key,
    value1=arbitrary_json,
    value2=arbitrary_json,
)
def test_update_key(key, value1, value2):
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        store[key] = value1

    with storage.transaction() as store:
        store[key] = value2

    with storage.transaction() as store:
        assert store[key] == value2


@cloned_redis_test(
    key=arbitrary_key,
    value=arbitrary_json,
)
def test_delete_key(key, value):
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        store[key] = value

    with storage.transaction() as store:
        del store[key]

    with storage.transaction() as store:
        assert key not in store


@cloned_redis_test(
    key=arbitrary_key,
    value=arbitrary_json,
)
def test_exceptions_back_out_writes(key, value):
    storage = ClonedRedisStore('')

    try:
        with storage.transaction() as store:
            store[key] = value
            raise RuntimeError()
    except RuntimeError:
        pass

    with storage.transaction() as store:
        assert key not in store


@cloned_redis_test(
    key=arbitrary_key,
    value1=arbitrary_json,
    value2=arbitrary_json,
    replacement_state=hypothesis.strategies.binary(),
)
def test_raises_retry_on_concurrent_write(
    key,
    value1,
    value2,
    replacement_state,
):
    storage = ClonedRedisStore('')

    with storage.transaction() as store:
        store[key] = value1

    with pytest.raises(Retry):
        with storage.transaction() as store:
            fakeredis.FakeStrictRedis().set(
                b'jacquard-store:state-key',
                replacement_state,
            )
            store[key] = value2
