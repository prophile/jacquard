import pprint

from jacquard.commands import BaseCommand
from jacquard.storage import open_engine
from jacquard.storage.utils import copy_data


class StorageDump(BaseCommand):
    plumbing = True
    help = "dump all objects in storage"

    def handle(self, config, options):
        with config.storage.transaction() as store:
            for key, value in store.items():
                print(key)
                print('=' * len(key))
                pprint.pprint(value)
                print()


class StorageImport(BaseCommand):
    help = "load stored data from another storage engine"

    def add_arguments(self, parser):
        parser.add_argument('engine', help="storage engine to load from")
        parser.add_argument('url', help="storage URL to load from")

    def handle(self, config, option):
        src = open_engine(option.engine, option.url)
        copy_data(src, config.storage)


class StorageFlush(BaseCommand):
    help = "clear everything in storage"

    def handle(self, config, option):
        with config.storage.transaction() as store:
            store.clear()
