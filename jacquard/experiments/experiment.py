"""Experiment definition abstraction class."""

import contextlib

import dateutil.parser

from jacquard.utils import check_keys
from jacquard.buckets.constants import NUM_BUCKETS

from .constraints import Constraints, ConstraintContext


class Experiment(object):
    """
    The definition of an experiment.

    This is essentially a plain-old-data class with utility methods for
    canonical serialisation and deserialisation of various flavours.
    """

    def __init__(
        self,
        experiment_id,
        branches,
        *,
        constraints=None,
        name=None,
        launched=None,
        concluded=None
    ):
        """Base constructor. Takes all the arguments."""
        self.id = experiment_id

        if not branches:
            raise ValueError("No branches given")

        branch_ids = set()
        for branch in branches:
            if 'id' not in branch:
                raise ValueError("Branch without ID")
            branch_id = branch['id']
            if branch_id in branch_ids:
                raise ValueError("Duplicate branch ID: %r" % branch_id)
            branch_ids.add(branch_id)
            if 'settings' not in branch:
                raise ValueError("No settings given")

        self.branches = branches

        if constraints is not None:
            self.constraints = constraints
        else:
            self.constraints = Constraints()

        self.name = name or self.id

        if not self.name:
            raise ValueError("Blank name")

        self.launched = launched
        self.concluded = concluded

        if self.concluded and not self.launched:
            raise ValueError("Experiment concluded but not launched")

        if self.concluded and self.launched and self.launched > self.concluded:
            raise ValueError("Experiment concluded before launch")

    @classmethod
    def from_json(cls, obj):
        """
        Create instance from a JSON-esque definition.

        Required keys: id, branches

        Optional keys: name, constraints, launched, concluded
        """
        kwargs = {}

        with contextlib.suppress(KeyError):
            kwargs['name'] = obj['name']

        with contextlib.suppress(KeyError):
            kwargs['constraints'] = Constraints.from_json(obj['constraints'])

        with contextlib.suppress(KeyError):
            kwargs['launched'] = dateutil.parser.parse(obj['launched'])

        with contextlib.suppress(KeyError):
            kwargs['concluded'] = dateutil.parser.parse(obj['concluded'])

        return cls(obj['id'], obj['branches'], **kwargs)

    @classmethod
    def from_store(cls, store, experiment_id):
        """Create instance from a store lookup by ID."""
        json_repr = dict(store['experiments/%s' % experiment_id])
        # Be resilient to missing ID
        if 'id' not in json_repr:
            json_repr['id'] = experiment_id
        return cls.from_json(json_repr)

    @classmethod
    def enumerate(cls, store):
        """
        Iterator over all named experiments in a store.

        Includes inactive experiments.
        """
        prefix = 'experiments/'

        for key in store:
            if not key.startswith(prefix):
                continue

            experiment_id = key[len(prefix):]
            yield cls.from_store(store, experiment_id)

    def to_json(self):
        """Serialise as canonical JSON."""
        representation = {
            'id': self.id,
            'branches': self.branches,
            'constraints': self.constraints.to_json(),
            'name': self.name,
            'launched': str(self.launched),
            'concluded': str(self.concluded),
        }

        if not representation['constraints']:
            del representation['constraints']

        if representation['name'] == self.id:
            del representation['name']

        if representation['launched'] == 'None':
            del representation['launched']

        if representation['concluded'] == 'None':
            del representation['concluded']

        return representation

    def save(self, store):
        """Save into the given store using the ID as the key."""
        store['experiments/%s' % self.id] = self.to_json()

    def branch(self, branch_id):
        """
        Get the branch with a given ID.

        In case of multiple branches with the same ID (which should Never Ever
        Happen), behaviour is undefined.

        If there is no such branch, LookupErrors will materialise.
        """
        branches_by_id = {x['id']: x for x in self.branches}

        check_keys((branch_id,), branches_by_id.keys(), exception=LookupError)
        return branches_by_id[branch_id]

    def branch_launch_configuration(self):
        """
        Launch configuration for the branches of this experiment.

        This is the format expected for the `branches` argument of `release`
        and `close`, to actually decide which buckets see this experiment.
        """
        def num_buckets(x):
            percent = x.get('percent', 100 // len(self.branches))
            return (NUM_BUCKETS * percent) // 100

        return [
            (
                x['id'],
                num_buckets(x),
                x['settings'],
            )
            for x in self.branches
        ]

    def includes_user(self, user_entry):
        """
        Check whether a user meets the experiment's constraints.

        A (hopefully constant time) predicate.
        """
        try:
            specialised_constraints = self._specialised_constraints
        except AttributeError:
            specialised_constraints = self.constraints.specialise(
                ConstraintContext(
                    era_start_date=self.launched,
                ),
            )
            self._specialised_constraints = specialised_constraints

        return specialised_constraints.matches_user(user_entry)
