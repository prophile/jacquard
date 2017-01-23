import datetime

import dateutil.tz
import pytest

from jacquard.directory.base import UserEntry
from jacquard.experiments.constraints import Constraints, ConstraintContext

UTC = dateutil.tz.tzutc()

CONTEXT = ConstraintContext(era_start_date=datetime.datetime(
    2017,
    1,
    1,
    tzinfo=UTC,
))

NAMED_OLD_USER = UserEntry(
    id='1',
    join_date=datetime.datetime(2016, 12, 1, tzinfo=UTC),
    tags=(),
)

NAMED_NEW_USER = UserEntry(
    id='2',
    join_date=datetime.datetime(2017, 1, 2, tzinfo=UTC),
    tags=(),
)


def tagged_user(*tags):
    return NAMED_NEW_USER._replace(tags=tuple(tags))


def constraint_match(description, user):
    return Constraints.from_json(description).matches_user(user, CONTEXT)


def test_constraints_from_empty_dict_raises_no_errors():
    Constraints.from_json({})


def test_constraints_allow_anonymous_users_by_default():
    assert constraint_match({}, None)


def test_constraints_allow_anonymous_users_with_anonymous_flag():
    assert constraint_match({'anonymous': True}, None)


def test_constraints_forbid_anonymous_users_without_anonymous_flag():
    assert not constraint_match({'anonymous': False}, None)


def test_constraints_permit_named_users_by_default():
    assert constraint_match({}, NAMED_NEW_USER)


def test_constraints_permit_named_users_with_named_flag():
    assert constraint_match({'named': True}, NAMED_NEW_USER)


def test_constraints_forbid_named_users_without_named_flag():
    assert not constraint_match({'named': False}, NAMED_NEW_USER)


def test_constraints_permit_old_users_by_default():
    assert constraint_match({}, NAMED_OLD_USER)


def test_constraints_permit_new_users_by_default():
    assert constraint_match({}, NAMED_NEW_USER)


def test_constraints_permit_old_users_with_era_old():
    assert constraint_match({'era': 'old'}, NAMED_OLD_USER)


def test_constraints_forbid_new_users_with_era_old():
    assert not constraint_match({'era': 'old'}, NAMED_NEW_USER)


def test_constraints_permit_anonymous_users_with_era_old():
    assert constraint_match({'era': 'old'}, None)


def test_constraints_permit_new_users_with_era_new():
    assert constraint_match({'era': 'new'}, NAMED_NEW_USER)


def test_constraints_forbid_old_users_with_era_new():
    assert not constraint_match({'era': 'new'}, NAMED_OLD_USER)


def test_constraints_permit_anonymous_users_with_era_new():
    assert constraint_match({'era': 'new'}, None)


def test_constraints_permit_users_with_required_tags():
    assert constraint_match({'required_tags': ('foo',)}, tagged_user('foo'))


def test_constraints_forbid_users_without_required_tags():
    assert not constraint_match({'required_tags': ('foo',)}, tagged_user('bar'))


def test_constraints_allow_anonymous_users_with_required_tags():
    assert constraint_match({'required_tags': ('foo',)}, None)


def test_constraints_require_all_tags_to_be_matched():
    assert not constraint_match({'required_tags': ('foo', 'bar')}, tagged_user('foo'))


def test_constraints_can_allow_irrelevant_tags_for_required():
    assert constraint_match({'required_tags': ('foo',)}, tagged_user('foo', 'bar'))


def test_constraints_forbid_users_with_excluded_tags():
    assert not constraint_match({'excluded_tags': ('foo',)}, tagged_user('foo'))


def test_constraints_permit_users_without_excluded_tags():
    assert constraint_match({'excluded_tags': ('foo',)}, tagged_user('bar'))


def test_constraints_allow_anonymous_users_with_excluded_tags():
    assert constraint_match({'excluded_tags': ('foo',)}, None)


def test_constraints_exclude_with_any_tags():
    assert not constraint_match({'excluded_tags': ('foo', 'bar')}, tagged_user('foo'))


def test_constraints_raise_valueerror_for_unknown_keys():
    with pytest.raises(ValueError):
        Constraints.from_json({'foo': 'bar'})
