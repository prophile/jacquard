import pprint

from jacquard.commands import BaseCommand

class StorageDump(BaseCommand):
    help = "dump all objects in storage"

    def add_arguments(self, parser):
        pass

    def handle(self, config, options):
        with config['storage'].transaction() as store:
            for key, value in store.items():
                print(key)
                print('=' * len(key))
                pprint.pprint(value)
                print()
