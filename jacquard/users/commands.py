import json
import contextlib

from jacquard.commands import BaseCommand


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
        with config['storage'].transaction() as store:
            defaults = dict(store.get('defaults', {}))

            if options.delete:
                with contextlib.suppress(KeyError):
                    del defaults[options.setting]

            else:
                try:
                    value = json.loads(options.value)
                except ValueError:
                    print(
                        "Could not decode %r: maybe you need quotes?" % options.value,
                    )
                    return

                defaults[options.setting] = value

            store['defaults'] = defaults
