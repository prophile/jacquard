from .base import KVStore, Retry


class RedisStore(KVStore):
    def __init__(self, connection_string):
        # Lazily import Redis
        import redis
        self.redis = redis.StrictRedis.from_url(connection_string)
        self.prefix = 'jacquard:'

    def begin(self):
        pass

    def rollback(self):
        self.redis.unwatch()

    def commit(self, changes, deletions):
        pipe = self.redis.pipeline(transaction=True)
        pipe.multi()

        for key, value in changes.items():
            pipe.set(key, value)

        for key in deletions:
            pipe.delete(key)

        try:
            pipe.execute()
        except Exception:  # TODO: specify
            raise Retry()

    def get(self, key):
        self.redis.watch(key)
        return self.redis.get(key)

    def keys(self):
        return [
            x.decode('utf-8')
            for x in self.redis.keys('{}*'.format(self.prefix))
        ]

    def encode_key(self, key):
        if ':' in key:
            raise ValueError("Invalid key %r" % key)
        return '{}{}'.format(self.prefix, key.replace('/', ':'))

    def decode_key(self, key):
        if not key.startswith(self.prefix):
            raise ValueError()
        return key[len(self.prefix):].replace(':', '/')
