"""Command-line utilities for storage subsystem."""

import pprint

from jacquard.commands import BaseCommand, CommandError
from jacquard.storage.utils import retrying, copy_data, open_engine


class StorageDump(BaseCommand):
    """
    Dump everything in the store to stdout.

    This is a debugging command, mainly for developer use.
    """

    plumbing = True
    help = "dump all objects in storage"

    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction(read_only=True) as store:
            for key, value in store.items():
                print(key)
                print('=' * len(key))
                pprint.pprint(value)
                print()


class StorageImport(BaseCommand):
    """
    Import all data from a given engine.

    This is a mechanism to make migrations between storage engines easier,
    when the time comes to upgrade. Also useful for restoring backups.
    """

    help = "load stored data from another storage engine"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument('engine', help="storage engine to load from")
        parser.add_argument('url', help="storage URL to load from")
        parser.add_argument(
            '--flush',
            action='store_true',
            help="flush out the previous data in storage",
        )

    @retrying
    def handle(self, config, option):
        """Run command."""
        src = open_engine(config, option.engine, option.url)
        copy_data(src, config.storage, flush=option.flush)


class StorageExport(BaseCommand):
    """
    Export all data to a given engine.

    This is a mechanism mainly for backups, although it may also be useful for
    migrations.
    """

    help = "export stored data to another storage engine"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument('engine', help="storage engine to save to")
        parser.add_argument('url', help="storage URL to save to")
        parser.add_argument(
            '--flush',
            action='store_true',
            help="erase storage destination before writing",
        )

    @retrying
    def handle(self, config, option):
        """Run command."""
        dst = open_engine(config, option.engine, option.url)
        copy_data(config.storage, dst, flush=option.flush)


class StorageFlush(BaseCommand):
    """
    Delete every key from the current store.

    A command which should be used with care for obvious reasons! Mainly useful
    before imports.

    There is an open question as to whether it would be wise to make this the
    default behaviour of importing.
    """

    help = "clear everything in storage"
    plumbing = True

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help=(
                "force Jacquard to actually do this despite its being "
                "obviously a bad idea"
            ),
        )

    @retrying
    def handle(self, config, option):
        """Run command."""
        if not option.force:
            raise CommandError(
                "This command would erase the database. If you are really "
                "sure this is something you want to do, add --force.",
            )

        with config.storage.transaction() as store:
            store.clear()
