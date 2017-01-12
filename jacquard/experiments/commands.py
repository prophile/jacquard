import datetime

from jacquard.commands import BaseCommand


class Launch(BaseCommand):
    help = "start an experiment running"

    def add_arguments(self, parser):
        parser.add_argument('experiment', help="experiment to launch")

    def handle(self, config, options):
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
    help = "finish an experiment"

    def add_arguments(self, parser):
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
