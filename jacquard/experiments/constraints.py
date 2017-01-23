import collections

ConstraintContext = collections.namedtuple(
    'ConstraintContext',
    ('era_start_date',),
)


class Constraints(object):
    def __init__(
        self,
        anonymous=True,
        named=True,
        era=None,
        required_tags=(),
        excluded_tags=(),
    ):
        self.include_anonymous = anonymous
        self.include_named = named
        self.era = era

        if era not in (None, 'old', 'new'):
            raise ValueError("Invalid era: %s" % era)

        self.required_tags = tuple(required_tags)
        self.excluded_tags = tuple(excluded_tags)

    @classmethod
    def from_json(cls, description):
        return cls(
            anonymous=description.get('anonymous', True),
            named=description.get('named', True),
            era=description.get('era'),
            required_tags=description.get('required_tags', ()),
            excluded_tags=description.get('excluded_tags', ()),
        )

    def to_json(self):
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
