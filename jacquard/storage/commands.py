import pprint

from jacquard.commands import BaseCommand
from jacquard.storage import open_engine


class StorageDump(BaseCommand):
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
        with config.storage.transaction() as dst_store:
            with src.transaction() as src_store:
                for key, value in src_store.items():
                    dst_store[key] = value


class StorageFlush(BaseCommand):
    help = "clear everything in storage"

    def handle(self, config, option):
        with config.storage.transaction() as store:
            store.clear()
