"""Built-in, core HTTP endpoints."""

from jacquard.users import get_settings
from jacquard.buckets import NUM_BUCKETS, Bucket, user_bucket
from jacquard.experiments import Experiment

from .base import Endpoint


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
    """
    Full experiment details.

    Includes all users in each branch.
    """

    url = '/experiments/<experiment>'

    def handle(self, experiment):
        """Dispatch request."""
        with self.config.storage.transaction(read_only=True) as store:
            experiment_config = Experiment.from_store(store, experiment)

            buckets = [
                Bucket.from_json(store.get('buckets/%s' % idx, ()))
                for idx in range(NUM_BUCKETS)
            ]

            branch_ids = [
                branch['id'] for branch in experiment_config.branches
            ]
            branches = {x: [] for x in branch_ids}

            relevant_settings = set()

            for branch_config in experiment_config.branches:
                relevant_settings.update(branch_config['settings'].keys())

            for user_entry in self.config.directory.all_users():
                if not experiment_config.includes_user(user_entry):
                    continue

                user_overrides = store.get('overrides/%s' % user_entry.id, {})

                if any(x in relevant_settings for x in user_overrides.keys()):
                    continue

                bucket = buckets[user_bucket(user_entry.id)]

                for branch_id, members in branches.items():
                    if bucket.covers([experiment_config.id, branch_id]):
                        members.append(user_entry.id)

        return {
            'id': experiment_config.id,
            'name': experiment_config.name,
            'launched': str(experiment_config.launched),
            'concluded': str(experiment_config.concluded),
            'branches': branches,
        }
