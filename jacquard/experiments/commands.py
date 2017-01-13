"""Command-line utilities for experiments subsystem."""

import json
import pathlib
import datetime

from jacquard.commands import BaseCommand


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
            try:
                experiment_config = store[
                    'experiments/%s' % options.experiment
                ]
            except KeyError:
                print("Experiment %r not configured" % options.experiment)
                return

            current_experiments = store.get('active-experiments', [])

            if options.experiment in current_experiments:
                print("Experiment %r already launched!" % options.experiment)
                return

            store['active-experiments'] = (
                current_experiments + [options.experiment]
            )

            experiment_config['launched'] = str(datetime.datetime.utcnow())
            store['experiments/%s' % options.experiment] = experiment_config


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
            try:
                experiment_config = store[
                    'experiments/%s' % options.experiment
                ]
            except KeyError:
                print("Experiment %r not configured" % options.experiment)
                return

            current_experiments = store.get('active-experiments', [])

            if options.experiment not in current_experiments:
                print("Experiment %r not launched!" % options.experiment)
                return

            current_experiments.remove(options.experiment)

            if options.promote_branch:
                defaults = store.get('defaults', {})

                # Find branch matching ID
                for branch in experiment_config['branches']:
                    if branch['id'] == options.branch:
                        defaults.update(branch['settings'])
                        break
                else:
                    print("Cannot find branch %r" % options.branch)
                    return

                store['defaults'] = defaults

            experiment_config['concluded'] = str(datetime.datetime.utcnow())
            store['experiments/%s' % options.experiment] = experiment_config

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
            definition = json.load(f)

        if not definition.get('branches'):
            print("No branches specified.")
            return

        experiment_id = definition['id']

        with config.storage.transaction() as store:
            live_experiments = store.get('active-experiments', ())

            if experiment_id in live_experiments:
                print(
                    "Experiment %r is live, refusing to edit" % experiment_id,
                )
                return

            store['experiments/%s' % experiment_id] = definition
