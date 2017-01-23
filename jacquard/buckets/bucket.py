import collections

from jacquard.experiments.constraints import Constraints

_Entry = collections.namedtuple(
    '_Entry',
    ('key', 'settings', 'constraints'),
)


class Bucket(object):
    def __init__(self, entries=()):
        self.entries = list(entries)

    @classmethod
    def from_json(cls, description):
        return cls(
            _Entry(
                key=key,
                settings=settings,
                constraints=Constraints.from_json(constraints),
            )
            for (key, settings, constraints) in description
        )

    def to_json(self):
        return [
            [x.key, x.settings, x.constraints.to_json()]
            for x in self.entries
        ]

    def get_settings(self, user_entry):
        settings = {}

        for entry in self.entries:
            if entry.constraints.matches_user(user_entry):
                settings.update(entry.settings)

    def add(self, key, settings, constraints):
        self.entries.append(_Entry(
            key=key,
            settings=settings,
            constraints=constraints,
        ))

    def remove(self, key):
        # Remove all matching entries, on equality
        self.entries = [
            x
            for x in self.entries
            if x.key != key
        ]
