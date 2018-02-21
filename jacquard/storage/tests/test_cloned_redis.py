import logging
import unittest
import unittest.mock

import pytest
import hypothesis.strategies

from jacquard.storage.exceptions import Retry
from jacquard.storage.cloned_redis import (
    ClonedRedisStore,
    resync_all_connections
)
from jacquard.storage.testing_utils import (
    StorageGauntlet,
    arbitrary_key,
    arbitrary_json
)

try:
    import fakeredis
except ImportError:
    fakeredis = None


def cloned_redis_storage_engine():
    fakeredis.FakeStrictRedis().flushall()
    resync_all_connections()

    with unittest.mock.patch(
        'redis.StrictRedis',
        fakeredis.FakeStrictRedis,
    ):
        return ClonedRedisStore('<fake redis connection>')


@pytest.mark.skipif(fakeredis is None, reason="fakeredis is not installed")
@unittest.mock.patch(
    'redis.StrictRedis',
    fakeredis.FakeStrictRedis,
)
class ClonedRedisGauntletTest(StorageGauntlet, unittest.TestCase):
    def open_storage(self):
        logging.basicConfig(level=logging.DEBUG)
        return cloned_redis_storage_engine()


@pytest.mark.skipif(fakeredis is None, reason="fakeredis is not installed")
@pytest.mark.filterwarnings('ignore:Mysteriously found')
#@hypothesis.given(
#    key=arbitrary_key,
#    value1=arbitrary_json,
#    value2=arbitrary_json,
#    replacement_state=hypothesis.strategies.uuids(),
#)
@unittest.mock.patch(
    'redis.StrictRedis',
    fakeredis.FakeStrictRedis,
)
def test_raises_retry_on_concurrent_write(
    key='',
    value1='1',
    value2='2',
    replacement_state='aaaa',
):
    storage = cloned_redis_storage_engine()
    logging.basicConfig(level=logging.DEBUG)

    with storage.transaction() as store:
        store[key] = value1

    with pytest.raises(Retry):
        with storage.transaction() as store:
            fakeredis.FakeStrictRedis().set(
                b'jacquard-store:state-key',
                str(replacement_state).encode('ascii'),
            )
            store[key] = value2
