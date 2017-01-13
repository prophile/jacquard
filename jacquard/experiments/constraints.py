"""
Experiment constraints evaluation.

An experiment may optionally contain a `constraints` dictionary defining which
subset of users the experiment is being run on. The keys which are currently
supported are:

anonymous
  A boolean, representing whether anonymous users (users for whom we have no
  information from the directory) are permitted.

joined_before
  A (string) date: only users who joined before this date are permitted.

joined_after
  A (string) date: only users who joined after this date are permitted.

required_tags
  A list: if specified, only users with all the given tags are permitted.

excluded_tags
  A list: if specified, only users without any of the given tags are permitted.

All these constraints are optional.

NB: If `anonymous` is True, which is the default, all anonymous users are
permitted, *regardless of other constraints*.
"""

import datetime
import dateutil.tz


FAR_FUTURE = datetime.datetime.max.replace(tzinfo=dateutil.tz.tzutc())
DISTANT_PAST = datetime.datetime.min.replace(tzinfo=dateutil.tz.tzutc())


def meets_constraints(constraints, user_entry):
    """
    Check whether a user meets the given constraints dict.

    A (hopefully constant time) predicate.
    """
    if user_entry is None:
        return constraints.get('anonymous', True)

    if (
        user_entry.join_date >
        constraints.get('joined_before', FAR_FUTURE)
    ):
        return False

    if (
        user_entry.join_date <
        constraints.get('joined_after', DISTANT_PAST)
    ):
        return False

    required_tags = constraints.get('required_tags', ())

    if (
        required_tags and
        any(x not in user_entry.tags for x in required_tags)
    ):
        return False

    excluded_tags = constraints.get('excluded_tags', ())

    if any(x in excluded_tags for x in user_entry.tags):
        return False

    return True
