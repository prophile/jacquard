import json
import pprint
import contextlib

from jacquard.commands import BaseCommand
from jacquard.users import get_settings


class SetDefault(BaseCommand):
    help = "set (or clear) a default setting"

    def add_arguments(self, parser):
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
    help = "control user overrides"

    def add_arguments(self, parser):
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
    help = "show settings for user"

    def add_arguments(self, parser):
        parser.add_argument(
            'user',
            help="user to show settings for",
            nargs='?',
        )

    def handle(self, config, options):
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
