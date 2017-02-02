"""Command-line utilities for experiments subsystem."""

import argparse
import datetime

import yaml
import dateutil.tz

from jacquard.commands import BaseCommand, CommandError
from jacquard.buckets.utils import close, release
from jacquard.storage.utils import retrying

from .experiment import Experiment


class Launch(BaseCommand):
    """
    Launch a given experiment.

    This is one of the main user commands. It promotes an experiment to being
    live, which effectively locks it out from being changed and starts putting
    users on its branches.
    """

    help = "start an experiment running"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument('experiment', help="experiment to launch")

    @retrying
    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            experiment = Experiment.from_store(store, options.experiment)

            current_experiments = store.get('active-experiments', [])

            if experiment.id in current_experiments:
                raise CommandError(
                    "Experiment %r already launched!" % experiment.id,
                )

            release(
                store,
                experiment.id,
                experiment.constraints,
                experiment.branch_launch_configuration(),
            )

            store['active-experiments'] = (
                current_experiments + [options.experiment]
            )

            experiment.launched = datetime.datetime.now(dateutil.tz.tzutc())
            experiment.save(store)


class Conclude(BaseCommand):
    """
    Conclude a given experiment.

    This is one of the main user commands. It demotes an experiment to no
    longer being live, records a conclusion date, and (optionally but
    strongly advised) promotes the settings from one of its branches into
    the defaults.
    """

    help = "finish an experiment"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument('experiment', help="experiment to conclude")
        mutex_group = parser.add_mutually_exclusive_group(required=True)
        mutex_group.add_argument(
            'branch',
            help="branch to promote to default",
            nargs='?',
        )
        mutex_group.add_argument(
            '--no-promote-branch',
            help="do not promote a branch to default",
            action='store_false',
            dest='promote_branch',
        )

    @retrying
    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            experiment = Experiment.from_store(store, options.experiment)

            current_experiments = store.get('active-experiments', [])

            if options.experiment not in current_experiments:
                raise CommandError(
                    "Experiment %r not launched!" % options.experiment,
                )

            current_experiments.remove(options.experiment)

            close(
                store,
                experiment.id,
                experiment.constraints,
                experiment.branch_launch_configuration(),
            )

            if options.promote_branch:
                defaults = store.get('defaults', {})

                # Find branch matching ID
                defaults.update(experiment.branch(options.branch)['settings'])

                store['defaults'] = defaults

            experiment.concluded = datetime.datetime.now(dateutil.tz.tzutc())
            experiment.save(store)

            store['active-experiments'] = current_experiments


class Load(BaseCommand):
    """
    Load an experiment definition from a file.

    This is obviously a pretty awful interface which will only do for this
    MVP state of the project, but currently this is the mechanism for loading
    an experiment definition.
    """

    help = "load an experiment definition from a file"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument(
            'files',
            nargs='+',
            type=argparse.FileType('r'),
            metavar='file',
            help="experiment definition",
        )
        parser.add_argument(
            '--skip-launched',
            action='store_true',
            help="do not error on launched experiments",
        )

    @retrying
    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            live_experiments = store.get('active-experiments', ())

            for file in options.files:
                definition = yaml.safe_load(file)

                experiment = Experiment.from_json(definition)

                if experiment.id in live_experiments:
                    if options.skip_launched:
                        continue

                    else:
                        raise CommandError(
                            "Experiment %r is live, refusing to edit" %
                            experiment.id,
                        )

                experiment.save(store)


class ListExperiments(BaseCommand):
    """
    List all experiments.

    Mostly useful in practice when one cannot remember the ID of an experiment.
    """

    help = "list all experiments"

    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction(read_only=True) as store:
            for experiment in Experiment.enumerate(store):
                if experiment.name == experiment.id:
                    title = experiment.id
                else:
                    title = '%s: %s' % (experiment.id, experiment.name)
                print(title)
                print('=' * len(title))
                print()
                if experiment.launched:
                    print('Launched: %s' % experiment.launched)
                    if experiment.concluded:
                        print('Concluded: %s' % experiment.concluded)
                    else:
                        print('In progress')
                else:
                    print('Not yet launched')
                print()
