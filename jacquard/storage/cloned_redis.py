"""Cloned-Redis storage engine."""

import time
import uuid
import pickle
import logging
import warnings
import threading

import redis

from .base import StorageEngine
from .exceptions import Retry

LOGGER = logging.getLogger('jacquard.storage.cloned_redis')


_REDIS_POOL = {}
_REDIS_POOL_LOCK = threading.Lock()


class _RedisDataPool(object):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = redis.StrictRedis.from_url(connection_string)
        self.lock = threading.Lock()
        self.pubsub_semaphore = threading.Semaphore(0)

        pubsub_thread = threading.Thread(
            target=self.pubsub_thread,
            daemon=True,
        )
        # PubSub thread also does the initial sync
        LOGGER.debug("Launching pubsub thread for %s", connection_string)
        pubsub_thread.start()

        LOGGER.debug("Waiting for pubsub semaphore...")
        self.pubsub_semaphore.acquire()
        LOGGER.debug("Done with connection init on %s", connection_string)

    def sync_update(self):
        with self.lock:
            self.state_key = self.connection.get(b'jacquard-store:state-key')
            LOGGER.debug("Got state key: %s", self.state_key)
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
        released_semaphore = False

        while True:
            try:
                subscriber = self.connection.pubsub()
                subscriber.subscribe('jacquard-store:state-key')
                LOGGER.debug(
                    "Subscribed to state changes for %s",
                    self.connection_string,
                )

                # Do this even on subsequent passes to resync
                LOGGER.debug("Doing resync...")
                self.sync_update()
                LOGGER.debug("Resync finished.")

                if not released_semaphore:
                    self.pubsub_semaphore.release()
                    LOGGER.debug("Released pubsub semaphore.")
                    released_semaphore = True

                while True:
                    message = subscriber.get_message(timeout=30)
                    if message is None:
                        # Poll for resync
                        current_state = self.connection.get(
                            b'jacquard-store:state-key',
                        )

                        if current_state != self.state_key:
                            LOGGER.info(
                                "Poll noticed state delta on %s: %s",
                                self.connection_string,
                                current_state,
                            )
                            # Use sync_update to recheck the key with the
                            # lock taken
                            self.sync_update()

                        continue

                    if message['type'] != 'message':
                        continue

                    with self.lock:
                        new_key = message['data']
                        if new_key == self.state_key:
                            continue

                        LOGGER.debug(
                            "Received state delta push: %s",
                            new_key,
                        )
                        self.state_key = new_key
                        self.load_state()
            except redis.exceptions.ConnectionError:
                LOGGER.warning(
                    "Disconnected from pub/sub on %s, "
                    "attempting reconnect in 10s",
                    self.connect_string,
                )
                # Wait and retry
                time.sleep(10)

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

        LOGGER.info("Opening new Redis data pool for: %s", connection_string)
        new_pool = _RedisDataPool(connection_string)
        _REDIS_POOL[connection_string] = new_pool
        return new_pool


def resync_all_connections():
    """For testing purposes, immediately resync all connections."""
    with _REDIS_POOL_LOCK:
        for connection in _REDIS_POOL.values():
            connection.sync_update()


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
            LOGGER.info(
                "Storage conflict: state has moved from %s to %s",
                self.state_key,
                cur_state_key,
            )
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

        LOGGER.debug(
            "Committed state delta: %s -> %s",
            self.state_key,
            new_state_key,
        )

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
