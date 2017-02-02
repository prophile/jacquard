"""Redis storage engine."""

import logging

import redis

from .base import StorageEngine
from .exceptions import Retry

LOGGER = logging.getLogger('jacquard.storage.redis')


class RedisStore(StorageEngine):
    """
    Redis storage engine.

    This engine has the benefit of having its insides easy to poke about with.

    While the codebase stores keys in a slash-based hierarchy, for the Redis
    backend `foo/bar` is encoded as `jacquard:foo:bar`. The values take their
    normal JSON form.
    """

    def __init__(self, connection_string):
        """
        Connect to Redis.

        The connection string is given as a URL configuring the connection.
        This is backed by `python-redis`, and the URL follows the format
        of `redis.StrictRedis.from_url`.
        """
        self.redis = redis.StrictRedis.from_url(connection_string)
        self.prefix = 'jacquard:'
        self.omit_watch = False

    def begin(self):
        """Begin transaction."""
        self.omit_watch = False

    def begin_read_only(self):
        """Begin read-only transaction."""
        self.omit_watch = True

    def rollback(self):
        """Roll back transaction."""
        if not self.omit_watch:
            self.redis.unwatch()

    def commit(self, changes, deletions):
        """Commit transaction."""
        pipe = self.redis.pipeline(transaction=True)
        pipe.multi()

        for key, value in changes.items():
            pipe.set(key, value)

        for key in deletions:
            pipe.delete(key)

        try:
            pipe.execute()
        except redis.exceptions.WatchError:
            LOGGER.exception("Redis key conflict")
            raise Retry()

    def get(self, key):
        """Get value."""
        if not self.omit_watch:
            self.redis.watch(key)
        return self.redis.get(key)

    def keys(self):
        """All keys."""
        return [
            x.decode('utf-8')
            for x in self.redis.keys('{}*'.format(self.prefix))
        ]

    def encode_key(self, key):
        """Encode key."""
        if ':' in key:
            raise ValueError("Invalid key %r" % key)
        return '{}{}'.format(self.prefix, key.replace('/', ':'))

    def decode_key(self, key):
        """Decode key."""
        if not key.startswith(self.prefix):
            raise ValueError()
        return key[len(self.prefix):].replace(':', '/')
