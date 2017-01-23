"""User constraints predicates."""

import collections

import dateutil.tz

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
        joined_before=None,
        joined_after=None,
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

        self.joined_before = joined_before
        self.joined_after = joined_after

    def __bool__(self):
        """Whether these constraints are non-universal."""
        if (
            self.era or
            self.required_tags or
            self.excluded_tags or
            self.joined_after or
            self.joined_before
        ):
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
            'joined_before',
            'joined_after',
        ))

        def get_maybe_date(key):
            try:
                string_date = description[key]
            except KeyError:
                return None

            return dateutil.parser.parse(string_date)

        return cls(
            anonymous=description.get('anonymous', True),
            named=description.get('named', True),
            era=description.get('era'),
            required_tags=description.get('required_tags', ()),
            excluded_tags=description.get('excluded_tags', ()),
            joined_before=get_maybe_date('joined_before'),
            joined_after=get_maybe_date('joined_after'),
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

        if self.joined_after:
            description['joined_after'] = str(self.joined_after)

        if self.joined_before:
            description['joined_before'] = str(self.joined_before)

        return description

    def specialise(self, context):
        """A copy, specialised for a given context."""
        joined_before_dates = []
        joined_after_dates = []

        if self.joined_before:
            joined_before_dates.append(self.joined_before)

        if self.joined_after:
            joined_after_dates.append(self.joined_after)

        if self.era == 'new':
            joined_after_dates.append(context.era_start_date)

        if self.era == 'old':
            joined_before_dates.append(context.era_start_date)

        if joined_before_dates:
            joined_before = min(joined_before_dates)
        else:
            joined_before = None

        if joined_after_dates:
            joined_after = max(joined_after_dates)
        else:
            joined_after = None

        return type(self)(
            anonymous=self.include_anonymous,
            named=self.include_named,
            joined_before=joined_before,
            joined_after=joined_after,
            required_tags=self.required_tags,
            excluded_tags=self.excluded_tags,
        )

    def matches_user(self, user, context=None):
        """Test matching a user, potentially in a given context."""
        if context is not None:
            return self.specialise(context).matches_user(user)

        if user is None:
            return self.include_anonymous

        if not self.include_named:
            return False

        if self.joined_before and user.join_date > self.joined_before:
            return False

        if self.joined_after and user.join_date < self.joined_after:
            return False

        if any(x not in user.tags for x in self.required_tags):
            return False

        if any(x in user.tags for x in self.excluded_tags):
            return False

        return True
