"""Implementation of `Bucket`."""

import collections

from jacquard.experiments.constraints import Constraints

_Entry = collections.namedtuple(
    '_Entry',
    ('key', 'settings', 'constraints'),
)


class Bucket(object):
    """A single partition of user space, with associated settings."""

    def __init__(self, entries=()):
        """Construct directly from a list of `_Entry` objects - internal."""
        self.entries = list(entries)

    @classmethod
    def from_json(cls, description):
        """Construct from JSON-encoded list as found in storage."""
        return cls(
            _Entry(
                key=key,
                settings=settings,
                constraints=Constraints.from_json(constraints),
            )
            for (key, settings, constraints) in description
        )

    def to_json(self):
        """Convert to JSON-encodable list."""
        return [
            [x.key, x.settings, x.constraints.to_json()]
            for x in self.entries
        ]

    def get_settings(self, user_entry):
        """Look up settings by user entry."""
        settings = {}

        for entry in self.entries:
            if (
                not entry.constraints or
                entry.constraints.matches_user(user_entry)
            ):
                settings.update(entry.settings)

        return settings

    def affected_settings(self):
        """All settings determined in this bucket."""
        return frozenset(
            y
            for x in self.entries
            for y in x.settings.keys()
        )

    def needs_constraints(self):
        """Whether any settings in this bucket involve constraint lookups."""
        return any(x.constraints for x in self.entries)

    def add(self, key, settings, constraints):
        """Add a new, keyed entry."""
        self.entries.append(_Entry(
            key=key,
            settings=settings,
            constraints=constraints,
        ))

    def remove(self, key):
        """Remove any matching, keyed entry."""
        self.entries = [
            x
            for x in self.entries
            if x.key != key
        ]

    def covers(self, key):
        """Whether a given key is covered under this bucket."""
        return any(
            x.key == key
            for x in self.entries
        )
