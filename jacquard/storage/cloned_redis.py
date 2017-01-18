"""Cloned-Redis storage engine."""

from .base import StorageEngine
from .exceptions import Retry

import time
import uuid
import redis
import pickle
import warnings
import threading


_REDIS_POOL = {}
_REDIS_POOL_LOCK = threading.Lock()


class _RedisDataPool(object):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = redis.StrictRedis.from_url(connection_string)
        self.lock = threading.Lock()

        self.sync_update()

        pubsub_thread = threading.Thread(
            target=self.pubsub_thread,
            daemon=True,
        )
        pubsub_thread.start()

        poll_thread = threading.Thread(
            target=self.poll_thread,
            daemon=True,
        )
        poll_thread.start()

    def sync_update(self):
        with self.lock:
            self.state_key = self.connection.get(b'jacquard-store:state-key')
            self.load_state()

    def load_state(self):
        if self.state_key:
            raw_data = self.connection.get(
                b'jacquard-store:state:%s' % self.state_key,
            )

            if raw_data is None:
                warnings.warn(
                    "Mysteriously found no data associated with state key: "
                    "%s" % self.state_key,
                )
                self.current_data = {}
            else:
                self.current_data = pickle.loads(raw_data)
        else:
            self.current_data = {}

    def pubsub_thread(self):
        while True:
            try:
                subscriber = self.connection.pubsub()
                subscriber.subscribe('jacquard-store:state-key')

                for message in subscriber.listen():
                    if message['type'] != 'message':
                        continue

                    with self.lock:
                        self.state_key = message['data']
                        self.load_state()
            except redis.exceptions.ConnectionError:
                # Wait and retry
                time.sleep(10)

    def poll_thread(self):
        while True:
            time.sleep(30)
            try:
                self.sync_update()
            except redis.exceptions.ConnectionError:
                # Silently ignore, wait for reconnection
                pass

    def get_state(self):
        with self.lock:
            return self.state_key, self.current_data

    def set_state(self, state_key, data):
        with self.lock:
            self.state_key = state_key
            self.current_data = data


def _get_shared_data(connection_string):
    with _REDIS_POOL_LOCK:
        try:
            return _REDIS_POOL[connection_string]
        except KeyError:
            pass

        new_pool = _RedisDataPool(connection_string)
        _REDIS_POOL[connection_string] = new_pool
        return new_pool


def destroy_shared_data():
    """For testing purposes, drop any shared data."""
    with _REDIS_POOL_LOCK:
        _REDIS_POOL.clear()


class ClonedRedisStore(StorageEngine):
    """
    Cloned Redis store.

    This is a storage engine backed by a Redis connection, akin to the `redis`
    storage engine. The difference is that this asynchronously keeps a copy of
    all data locally, updating using Redis pubsub.

    While this has the disadvantage of keeping everything in memory and of
    storing all the data in one Redis key, it has the distinct advantage of
    being extremely fast to serve data locally (no network round-trips needed)
    and is somewhat more robust to transient downtime on Redis's part.
    """

    def __init__(self, connection_string):
        """
        Connect to Redis.

        The connection string is given as a URL configuring the connection.
        This is backed by `python-redis`, and the URL follows the format
        of `redis.StrictRedis.from_url`.
        """
        self.connection_string = connection_string
        self.pool = _get_shared_data(connection_string)

    def _encode_redis_data(self, data):
        return pickle.dumps(data, protocol=4)

    def begin(self):
        """Begin transaction."""
        self.state_key, self.transaction_data = self.pool.get_state()

    def commit(self, updates, deletions):
        """Commit transaction."""
        # Make synchronous connection
        connection = redis.StrictRedis.from_url(self.connection_string)

        # Validate that the state key has not changed
        connection.watch(b'jacquard-store:state-key')
        cur_state_key = connection.get(b'jacquard-store:state-key')

        if cur_state_key != self.state_key:
            connection.unwatch()
            self.pool.sync_update()
            del self.transaction_data
            del self.state_key
            raise Retry()

        new_state_key = str(uuid.uuid4()).encode('ascii')

        # Write back new state
        self.transaction_data.update(updates)

        for deletion in deletions:
            try:
                del self.transaction_data[deletion]
            except KeyError:
                pass

        raw_data = self._encode_redis_data(self.transaction_data)

        connection.set(b'jacquard-store:state:%s' % new_state_key, raw_data)

        # Update the current state pointer and notify
        pipeline = connection.pipeline(transaction=True)
        pipeline.set(b'jacquard-store:state-key', new_state_key)
        pipeline.publish('jacquard-store:state-key', new_state_key)

        if cur_state_key:
            # Expire the old state in half an hour.
            pipeline.expire(b'jacquard-store:state:%s' % cur_state_key, 1800)

        try:
            pipeline.execute()
        except Exception:
            del self.transaction_data
            del self.state_key
            raise Retry()

        self.pool.set_state(new_state_key, self.transaction_data)

        del self.transaction_data
        del self.state_key

    def rollback(self):
        """Roll back transaction."""
        del self.transaction_data
        del self.state_key

    def get(self, key):
        """Get key."""
        return self.transaction_data.get(key)

    def keys(self):
        """All keys."""
        return self.transaction_data.keys()
