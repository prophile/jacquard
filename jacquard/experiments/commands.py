"""Command-line utilities for experiments subsystem."""

import yaml
import pathlib
import datetime
import dateutil.tz

from jacquard.commands import BaseCommand
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

    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            experiment = Experiment.from_store(store, options.experiment)

            current_experiments = store.get('active-experiments', [])

            if experiment.id in current_experiments:
                print("Experiment %r already launched!" % experiment.id)
                return

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

    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
            experiment = Experiment.from_store(store, options.experiment)

            current_experiments = store.get('active-experiments', [])

            if options.experiment not in current_experiments:
                print("Experiment %r not launched!" % options.experiment)
                return

            current_experiments.remove(options.experiment)

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
    an experiment definition. There are some basic checks on having nonzero
    branches and not altering live experiments but otherwise this is not
    particularly robust code and needs replacing.

    At least loading from YAML might be a good start...
    """

    help = "load an experiment definition from a file"

    def add_arguments(self, parser):
        """Add argparse arguments."""
        parser.add_argument(
            'file',
            type=pathlib.Path,
            help="experiment definition",
        )

    def handle(self, config, options):
        """Run command."""
        with options.file.open('r') as f:
            definition = yaml.load(f)

        if not definition.get('branches'):
            print("No branches specified.")
            return

        experiment = Experiment.from_json(definition)

        with config.storage.transaction() as store:
            live_experiments = store.get('active-experiments', ())

            if experiment.id in live_experiments:
                print(
                    "Experiment %r is live, refusing to edit" % experiment.id,
                )
                return

            experiment.save(store)


class ListExperiments(BaseCommand):
    """
    List all experiments.

    Mostly useful in practice when one cannot remember the ID of an experiment.
    """

    help = "list all experiments"

    def handle(self, config, options):
        """Run command."""
        with config.storage.transaction() as store:
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
