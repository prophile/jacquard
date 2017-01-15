import contextlib
import dateutil.parser


class Experiment(object):
    def __init__(self, experiment_id, branches, *, constraints=None, name=None, launched=None, concluded=None):
        self.id = experiment_id
        self.branches = branches
        self.constraints = constraints or {}
        self.name = name or self.id
        self.launched = launched
        self.concluded = concluded

    @classmethod
    def from_json(cls, obj):
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
        json_repr = dict(store['experiments/%s' % experiment_id])
        # Be resilient to missing ID
        if 'id' not in json_repr:
            json_repr['id'] = experiment_id
        return cls.from_json(json_repr)

    def to_json(self):
        representation = {
            'id': self.id,
            'branches': self.branches,
            'constraints': self.constraints,
            'name': self.name,
            'launched': self.launched,
            'concluded': self.concluded,
        }

        if not representation['constraints']:
            del representation['constraints']

        if representation['name'] == self.id:
            del representation['name']

        if representation['launched'] is None:
            del representation['launched']

        if representation['concluded'] is None:
            del representation['concluded']

        return representation

    def save(self, store):
        store['experiments/%s' % self.id] = self.to_json()

    def branch(self, branch_id):
        for branch in self.branches:
            if branch['id'] == branch_id:
                return branch
        raise LookupError("No such branch: %r" % branch_id)
