import unittest

from jacquard.storage.dummy import DummyStore
from jacquard.storage.testing_utils import StorageGauntlet


class DummyGauntletTest(StorageGauntlet, unittest.TestCase):
    def open_storage(self):
        return DummyStore('')
