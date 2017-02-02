import unittest
import functools
import unittest.mock

import pytest

from jacquard.storage.redis import RedisStore
from jacquard.storage.testing_utils import StorageGauntlet

try:
    import fakeredis
except ImportError:
    fakeredis = None


@pytest.mark.skipif(fakeredis is None, reason="fakeredis is not installed")
class RedisGauntletTest(StorageGauntlet, unittest.TestCase):
    def open_storage(self):
        fakeredis.FakeStrictRedis().flushall()
        with unittest.mock.patch(
            'redis.StrictRedis',
            fakeredis.FakeStrictRedis,
        ):
            return RedisStore('')
