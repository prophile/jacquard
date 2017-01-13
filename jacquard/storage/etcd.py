"""etcd storage engine."""

import json
import threading
import urllib.parse

from .base import StorageEngine
from .exceptions import Retry

_CONNECTION_POOL = {}
_CONNECTION_POOL_LOCK = threading.Lock()


class _EtcdConnection(object):
    def __init__(self, connection_string):
        import etcd
        self.etcd = etcd

        parsed_url = urllib.parse.urlparse(connection_string)
        self.client = etcd.Client(
            host=parsed_url.hostname or 'localhost',
            port=parsed_url.port or 2379,
            username=parsed_url.username,
            password=parsed_url.password,
            protocol=parsed_url.scheme,
            allow_reconnect=True,
        )
        self.path = parsed_url.path

        self._get_sync()
        self._launch_stream_thread()

    def _get_sync(self):
        try:
            result = self.client.read(self.path)

            self.data = result.value
            self.index = result.modifiedIndex

        except self.etcd.EtcdKeyNotFound:
            self.data = '{}'
            self.index = None

    def _launch_stream_thread(self):
        thr = threading.Thread(target=self._stream_changes, daemon=True)
        thr.start()

    def _stream_changes(self):
        for event in self.client.eternal_watch(self.path):
            self.data = event.value
            self.index = event.modifiedIndex

    def get(self):
        return self.data, self.index

    def put(self, data, index):
        if index != self.index:
            return False

        if index is None:
            kwargs = {'prevExist': False}
        else:
            kwargs = {'prevIndex': index}

        try:
            self.client.write(self.path, data, **kwargs)
        except self.etcd.EtcdKeyError:
            self._get_sync()
            return False

        return True


def _get_connection(connection_string):
    with _CONNECTION_POOL_LOCK:
        try:
            return _CONNECTION_POOL[connection_string]
        except KeyError:
            pass

        connection = _EtcdConnection(connection_string)

        _CONNECTION_POOL[connection_string] = connection
        return connection


class EtcdStore(StorageEngine):
    """etcd storage engine."""

    def __init__(self, connection_string):
        """
        Initialise connection.

        The connection string is given as a URL. The etcd store only uses a
        single key in etcd, and the key is given in the path. The netloc and
        scheme are used to determine the connection.

        For instance, to connect unencrypted to a local etcd instance and use
        the path /jacquard/faces, the URL would be:

        `http://localhost:2379/jacquard/faces`
        """
        self.connection = _get_connection(connection_string)

    def begin(self):
        """Begin transaction."""
        data, self.index = self.connection.get()
        self.data = json.loads(data)

    def rollback(self):
        """Roll back transaction."""
        del self.data
        del self.index

    def commit(self, changes, deletions):
        """Commit transaction."""
        self.data.update(changes)

        for key in deletions:
            try:
                del self.data[key]
            except KeyError:
                pass

        success = self.connection.put(json.dumps(self.data), self.index)

        del self.data
        del self.index

        if not success:
            raise Retry()

    def get(self, key):
        """Get value."""
        return self.data.get(key)

    def keys(self):
        """All keys."""
        return self.data.keys()
