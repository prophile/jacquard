"""Built-in, core HTTP endpoints."""

from werkzeug.exceptions import MethodNotAllowed

from jacquard.odm import EMPTY, Session
from jacquard.users import get_settings
from jacquard.buckets import NUM_BUCKETS, Bucket, user_bucket
from jacquard.experiments import Experiment
from jacquard.service.base import Endpoint


class Root(Endpoint):
    """
    API root.

    Essentially a directory of the main endpoints available.
    """

    url = '/'

    def handle(self):
        """Dispatch request."""
        return {
            'users': self.reverse('user', user=':user'),
            'experiments': self.reverse('experiments-overview'),
            'defaults': self.reverse('defaults'),
        }


class User(Endpoint):
    """
    User settings lookup.

    Gets the JSON representation of the current experiment settings for a
    given user ID.
    """

    url = '/users/<user>'

    def handle(self, user):
        """Dispatch request."""
        settings = get_settings(
            user,
            self.config.storage,
            self.config.directory,
        )

        return {**settings, 'user': user}


class ExperimentsOverview(Endpoint):
    """
    Experiment status overview.

    Gives basic details on all experiments in the system, regardless of state.
    """

    url = '/experiments'

    def handle(self):
        """Dispatch request."""
        with self.config.storage.transaction(read_only=True) as store:
            active_experiments = store.get('active-experiments', ())
            experiments = list(Experiment.enumerate(store))

        return [
            {
                'id': experiment.id,
                'url': self.reverse('experiment', experiment=experiment.id),
                'state':
                    'active'
                    if experiment.id in active_experiments
                    else 'inactive',
                'name': experiment.name,
            }
            for experiment in experiments
        ]


class ExperimentDetail(Endpoint):
    """Full experiment details."""

    url = '/experiments/<experiment>'

    def handle(self, experiment):
        """Dispatch request."""
        with self.config.storage.transaction(read_only=True) as store:
            experiment_config = Experiment.from_store(store, experiment)

            branches = [x['id'] for x in experiment_config.branches]

        return {
            'id': experiment_config.id,
            'name': experiment_config.name,
            'launched': str(experiment_config.launched),
            'concluded': str(experiment_config.concluded),
            'branches': branches,
            'partition': self.reverse(
                'experiment-partition',
                experiment=experiment,
            ),
        }


class ExperimentPartition(Endpoint):
    """Grouping of users by branch in a given experiment."""

    url = '/experiments/<experiment>/partition'

    def handle(self, experiment):
        """Dispatch request."""
        if self.request.method != 'POST':
            raise MethodNotAllowed()

        user_ids = self.request.form.getlist('u')

        with self.config.storage.transaction(read_only=True) as store:
            session = Session(store)

            experiment_config = Experiment.from_store(store, experiment)

            buckets = [
                session.get(Bucket, idx, default=EMPTY)
                for idx in range(NUM_BUCKETS)
            ]

            branch_ids = [
                branch['id'] for branch in experiment_config.branches
            ]
            branches = {x: [] for x in branch_ids}

            relevant_settings = set()

            for branch_config in experiment_config.branches:
                relevant_settings.update(branch_config['settings'].keys())

            for user_id in user_ids:
                user_entry = self.config.directory.lookup(user_id)

                if not experiment_config.includes_user(user_entry):
                    continue

                user_overrides = store.get(
                    'overrides/{user_id}'.format(user_id=user_id),
                    {},
                )

                if any(x in relevant_settings for x in user_overrides.keys()):
                    continue

                bucket = buckets[user_bucket(user_id)]

                for branch_id, members in branches.items():
                    if bucket.covers([experiment_config.id, branch_id]):
                        members.append(user_id)

        return {'branches': branches}


class Defaults(Endpoint):
    """
    Global defaults lookup.

    Potentially useful for archival.
    """

    url = '/defaults'

    def handle(self):
        """Dispatch request."""
        with self.config.storage.transaction(read_only=True) as store:
            return store.get('defaults', {})
