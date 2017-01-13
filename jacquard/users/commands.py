"""General user settings commands."""

import json
import pprint
import contextlib

from jacquard.commands import BaseCommand
from jacquard.users import get_settings


class SetDefault(BaseCommand):
    """
    Manipulate the current defaults.

    This is one of the main commands used when adding new features. The
    defaults are, as their name suggests, shared between all users.
    """

    help = "set (or clear) a default setting"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument('setting', help="setting key")
        mutex_group = parser.add_mutually_exclusive_group(required=True)
        mutex_group.add_argument(
            'value',
            help="value to set",
            nargs='?',
        )
        mutex_group.add_argument(
            '-d',
            '--delete',
            help="clear the associated value",
            action='store_true',
        )

    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            defaults = dict(store.get('defaults', {}))

            if options.delete:
                with contextlib.suppress(KeyError):
                    del defaults[options.setting]

            else:
                try:
                    value = json.loads(options.value)
                except ValueError:
                    print(
                        "Could not decode %r: maybe you need quotes?" %
                        options.value,
                    )
                    return

                defaults[options.setting] = value

            store['defaults'] = defaults


class Override(BaseCommand):
    """
    Configure per-user overrides.

    Occasionally it is useful to set specific settings for specific users,
    overriding the defaults and any experiments they may be in. This could
    be for testing purposes on test or admin accounts, or even to give specific
    users experiences they want in the name of customer support.
    """

    help = "control user overrides"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument('user', help="user to override for")
        parser.add_argument('setting', help="setting key")
        mutex_group = parser.add_mutually_exclusive_group(required=False)
        mutex_group.add_argument(
            'value',
            help="value to set",
            nargs='?',
        )
        mutex_group.add_argument(
            '-d',
            '--delete',
            help="clear the associated value",
            action='store_true',
        )

    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            key = 'overrides/%s' % options.user

            overrides = dict(store.get(key, {}))

            if options.delete:
                with contextlib.suppress(KeyError):
                    del overrides[options.setting]

                if overrides == {}:
                    with contextlib.suppress(KeyError):
                        del store[key]
                else:
                    store[key] = overrides

            elif options.value:
                try:
                    value = json.loads(options.value)
                except ValueError:
                    print(
                        "Could not decode %r: maybe you need quotes?" %
                        options.value,
                    )
                    return

                overrides[options.setting] = value
                store[key] = overrides

            else:
                pprint.pprint(overrides)


class Show(BaseCommand):
    """
    Show current settings for a given user.

    This mirrors the main endpoint in the HTTP API and useful to see at a
    glance what a specific user's settings are. Also can be used with no
    arguments to show the current defaults.
    """

    help = "show settings for user"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument(
            'user',
            help="user to show settings for",
            nargs='?',
        )

    def handle(self, config, options):
        """Run command."""
        if options.user:
            settings = get_settings(
                options.user,
                config.storage,
                config.directory,
            )
        else:
            with config.storage.transaction() as store:
                settings = store.get('defaults', {})

        pprint.pprint(settings)
