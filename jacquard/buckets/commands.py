import yaml

from jacquard.commands import BaseCommand
from jacquard.experiments.constraints import Constraints
from jacquard.buckets.utils import release, close
from jacquard.buckets.constants import NUM_BUCKETS


class Rollout(BaseCommand):
    help = "partially roll out a feature"

    def add_arguments(self, parser):
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
        rollout_key = 'rollout:%s' % options.setting
        no_constraints = Constraints()

        value = yaml.load(options.value)
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
