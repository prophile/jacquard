"""Supporting classes to represent single keys within buckets."""

import collections

from jacquard.constraints import Constraints

Entry = collections.namedtuple(
    'Entry',
    ('key', 'settings', 'constraints'),
)


def decode_entry(json):
    """Convert from a JSON-representation to an Entry."""
    key, settings, constraints = json
    return Entry(
        key=key,
        settings=settings,
        constraints=Constraints.from_json(constraints),
    )


def encode_entry(entry):
    """Convert from an entry to a JSON-representation."""
    return [
        entry.key,
        entry.settings,
        entry.constraints.to_json(),
    ]
