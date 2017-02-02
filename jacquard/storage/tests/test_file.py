import unittest

from jacquard.storage.file import FileStore
from jacquard.storage.testing_utils import StorageGauntlet


class FileGauntletTest(StorageGauntlet, unittest.TestCase):
    def open_storage(self):
        return FileStore(':memory:')


def test_exceptions_back_out_writes():
    storage = FileStore(':memory:')

    try:
        with storage.transaction() as store:
            store['foo'] = "Blah"
            raise RuntimeError()
    except RuntimeError:
        pass

    with storage.transaction() as store:
        assert 'foo' not in store
