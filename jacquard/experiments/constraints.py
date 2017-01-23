"""User constraints predicates."""

import collections

from jacquard.utils import check_keys

ConstraintContext = collections.namedtuple(
    'ConstraintContext',
    ('era_start_date',),
)


ConstraintContext.__doc__ = """Context for evaluating constraints."""

ConstraintContext.era_start_date.__doc__ = """
Considered "start date" of the era of this experiment.

Used in the `era` key. Generally experiment launch date.
"""


class Constraints(object):
    """
    Constraints definition.

    This can filter by:

    anonymous
      Whether anonymous users can be considered under these constraints. A
      strong note of caution: if anonymous users are included, they are
      included *without regard to any other constraint*.

    named
      Whether named users can be considered under these constraints.

    era
      The era, 'old' or 'new' relative to the experiment start date, for users
      included in these constraints.

    required_tags
      A sequence of tags, all of which are required for a user to be in these
      constraints.

    excluded_tags
      A sequence of tags, any of which will exclude a user from this test.
    """

    def __init__(
        self,
        anonymous=True,
        named=True,
        era=None,
        required_tags=(),
        excluded_tags=(),
    ):
        """
        Manual constructor.

        Can be called with no arguments for the "universal constraints" - the
        constraints which are equivalent to unconditionally matching users.

        Generally prefer `.from_json`.
        """
        self.include_anonymous = anonymous
        self.include_named = named
        self.era = era

        if era not in (None, 'old', 'new'):
            raise ValueError("Invalid era: %s" % era)

        self.required_tags = tuple(required_tags)
        self.excluded_tags = tuple(excluded_tags)

    def __bool__(self):
        """Whether these constraints are non-universal."""
        if self.era or self.required_tags or self.excluded_tags:
            return True

        if not self.include_named:
            return True

        if not self.include_anonymous:
            return True

        return False

    @classmethod
    def from_json(cls, description):
        """Generate constraints from a JSON description."""
        check_keys(description.keys(), (
            'anonymous',
            'named',
            'era',
            'required_tags',
            'excluded_tags',
        ))

        return cls(
            anonymous=description.get('anonymous', True),
            named=description.get('named', True),
            era=description.get('era'),
            required_tags=description.get('required_tags', ()),
            excluded_tags=description.get('excluded_tags', ()),
        )

    def to_json(self):
        """
        Produce a JSON description.

        A pseudo-inverse of `.from_json`.
        """
        description = {
            'anonymous': self.include_anonymous,
            'named': self.include_named,
        }

        if self.era is not None:
            description['era'] = self.era

        if self.required_tags:
            description['required_tags'] = self.required_tags

        if self.excluded_tags:
            description['excluded_tags'] = self.excluded_tags

        return description

    def matches_user(self, user, context):
        """Test matching a user in a given context."""
        if user is None:
            return self.include_anonymous

        if not self.include_named:
            return False

        minimum_join_date = None
        maximum_join_date = None

        if self.era == 'old':
            maximum_join_date = context.era_start_date

        if self.era == 'new':
            minimum_join_date = context.era_start_date

        if minimum_join_date and user.join_date < minimum_join_date:
            return False

        if maximum_join_date and user.join_date > maximum_join_date:
            return False

        if any(x not in user.tags for x in self.required_tags):
            return False

        if any(x in user.tags for x in self.excluded_tags):
            return False

        return True
