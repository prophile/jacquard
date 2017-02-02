import unittest

from jacquard.storage.db import DBStore
from jacquard.storage.testing_utils import StorageGauntlet


class DBStorageGauntlet(StorageGauntlet, unittest.TestCase):
    def open_storage(self):
        return DBStore('sqlite://')
