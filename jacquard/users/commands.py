"""General user settings commands."""

import sys
import contextlib

import yaml

from jacquard.users import get_settings
from jacquard.storage import retrying
from jacquard.commands import BaseCommand, CommandError


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
        parser.add_argument(
            '--add',
            help="skip any keys which already exist in the database",
            action='store_true',
        )

    @retrying
    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            defaults = dict(store.get('defaults', {}))

            any_changes = False

            if options.delete:
                with contextlib.suppress(KeyError):
                    del defaults[options.setting]
                    any_changes = True

            else:
                try:
                    value = yaml.safe_load(options.value)
                except ValueError:
                    raise CommandError("Could not decode {value!r}".format(
                        value=options.value,
                    ))

                if not options.add or options.setting not in defaults:
                    defaults[options.setting] = value
                    any_changes = True

            if any_changes:
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

    @retrying
    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            key = 'overrides/{user_id}'.format(user_id=options.user)

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
                    value = yaml.safe_load(options.value)
                except ValueError:
                    raise CommandError("Could not decode {value!r}".format(
                        value=options.value,
                    ))

                overrides[options.setting] = value
                store[key] = overrides

            else:
                yaml.dump(overrides, sys.stdout, default_flow_style=False)


class OverrideClear(BaseCommand):
    """Clear all overrides, per-user or per-setting."""

    help = "erase user overrides in bulk"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        mutex_group = parser.add_mutually_exclusive_group(required=True)
        mutex_group.add_argument(
            'user',
            help="user ID to wipe overrides for",
            nargs='?',
        )
        mutex_group.add_argument(
            '-s',
            '--setting',
            help="setting to wipe overrides for",
        )

    def _clear_overrides_for_user(self, store, user):
        key = 'overrides/{user_id}'.format(user_id=user)

        with contextlib.suppress(KeyError):
            del store[key]

    def _clear_overrides_for_setting(self, store, setting):
        prefix = 'overrides/'

        for key in store:
            if not key.startswith(prefix):
                continue

            overrides = dict(store[key])

            try:
                del overrides[setting]
            except KeyError:
                continue

            if overrides:
                store[key] = overrides
            else:
                # All overrides gone, delete this key from storage entirely
                del store[key]

    @retrying
    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            if options.user:
                self._clear_overrides_for_user(store, options.user)
            else:
                self._clear_overrides_for_setting(store, options.setting)


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
            with config.storage.transaction(read_only=True) as store:
                settings = store.get('defaults', {})

        yaml.dump(settings, sys.stdout, default_flow_style=False)
