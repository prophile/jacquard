"""Command-line utilities for bucket subsystem."""

import yaml

from jacquard.commands import BaseCommand
from jacquard.buckets.utils import close, release
from jacquard.buckets.constants import NUM_BUCKETS
from jacquard.experiments.constraints import Constraints


class Rollout(BaseCommand):
    """
    Roll out feature or setting.

    This command is used for partial deployment of a feature, generally for
    piloting something before rollout or a test in order to check for
    show-stopping bugs.
    """

    help = "partially roll out a feature"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument('setting', help="setting name")
        parser.add_argument('value', help="value to roll out")

        command = parser.add_mutually_exclusive_group(required=True)

        command.add_argument(
            '--rollback',
            action='store_true',
            help="roll back to the defaults",
        )

        command.add_argument(
            '--commit',
            action='store_true',
            help="commit to this option",
        )

        command.add_argument(
            '--percent',
            type=int,
            default=0,
            help="do a staged rollout",
        )

    def handle(self, config, options):
        """Run command."""
        rollout_key = 'rollout:%s' % options.setting
        no_constraints = Constraints()

        value = yaml.safe_load(options.value)
        settings = {options.setting: value}

        buckets_per_percent = NUM_BUCKETS // 100

        branch_configuration = (
            ('__ROLLOUT__', buckets_per_percent * options.percent, settings),
        )

        with config.storage.transaction() as store:
            if options.rollback or options.commit:
                close(
                    store,
                    rollout_key,
                    no_constraints,
                    branch_configuration,
                )

                if options.commit:
                    defaults = dict(store.get('defaults', {}))
                    defaults.update(settings)
                    store['defaults'] = defaults
            else:
                release(
                    store,
                    rollout_key,
                    no_constraints,
                    branch_configuration,
                )
