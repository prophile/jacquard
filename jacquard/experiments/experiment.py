"""Experiment definition abstraction class."""

import contextlib
import dateutil.parser


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
        self.branches = branches
        self.constraints = constraints or {}
        self.name = name or self.id
        self.launched = launched
        self.concluded = concluded

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
            kwargs['constraints'] = obj['constraints']

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
            'constraints': self.constraints,
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
        for branch in self.branches:
            if branch['id'] == branch_id:
                return branch
        raise LookupError("No such branch: %r" % branch_id)

    def includes_user(self, user_entry):
        """
        Check whether a user meets the experiment's constraints dict.

        A (hopefully constant time) predicate.

        The keys which are currently supported are:

        anonymous
          A boolean, representing whether anonymous users (users for whom we have no
          information from the directory) are permitted.

        required_tags
          A list: if specified, only users with all the given tags are permitted.

        excluded_tags
          A list: if specified, only users without any of the given tags are permitted.

        All these constraints are optional.

        NB: If `anonymous` is True, which is the default, all anonymous users are
        permitted, *regardless of other constraints*.
        """
        if user_entry is None:
            return self.constraints.get('anonymous', True)

        required_tags = self.constraints.get('required_tags', ())

        if (
                    required_tags and
                    any(x not in user_entry.tags for x in required_tags)
        ):
            return False

        excluded_tags = self.constraints.get('excluded_tags', ())

        if any(x in excluded_tags for x in user_entry.tags):
            return False

        return True

