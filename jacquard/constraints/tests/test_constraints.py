import datetime

import pytest
import dateutil.tz

from jacquard.constraints import Constraints, ConstraintContext
from jacquard.directory.base import UserEntry

UTC = dateutil.tz.tzutc()

CONTEXT = ConstraintContext(era_start_date=datetime.datetime(2017, 1, 1, tzinfo=UTC))

NAMED_OLD_USER = UserEntry(
    id="1", join_date=datetime.datetime(2016, 12, 1, tzinfo=UTC), tags=()
)

NAMED_NEW_USER = UserEntry(
    id="2", join_date=datetime.datetime(2017, 1, 2, tzinfo=UTC), tags=()
)


def tagged_user(*tags):
    return NAMED_NEW_USER._replace(tags=tuple(tags))


def constraint_match(description, user):
    return Constraints.from_json(description).matches_user(user, CONTEXT)


def is_disjoint(c1, c2):
    return Constraints.from_json(c1).is_provably_disjoint_from_constraints(
        Constraints.from_json(c2)
    )


def test_constraints_require_timezones():
    with pytest.raises(ValueError):
        Constraints.from_json({"joined_before": "2018-05-05 10:00"})


def test_constraints_from_empty_dict_raises_no_errors():
    Constraints.from_json({})


def test_constraints_deny_anonymous_users_by_default():
    assert not constraint_match({}, None)


def test_constraints_permit_named_users_by_default():
    assert constraint_match({}, NAMED_NEW_USER)


def test_constraints_permit_old_users_by_default():
    assert constraint_match({}, NAMED_OLD_USER)


def test_constraints_permit_new_users_by_default():
    assert constraint_match({}, NAMED_NEW_USER)


def test_constraints_permit_old_users_with_era_old():
    assert constraint_match({"era": "old"}, NAMED_OLD_USER)


def test_constraints_forbid_new_users_with_era_old():
    assert not constraint_match({"era": "old"}, NAMED_NEW_USER)


def test_constraints_permit_new_users_with_era_new():
    assert constraint_match({"era": "new"}, NAMED_NEW_USER)


def test_constraints_forbid_old_users_with_era_new():
    assert not constraint_match({"era": "new"}, NAMED_OLD_USER)


def test_constraints_permit_users_with_required_tags():
    assert constraint_match({"required_tags": ("foo",)}, tagged_user("foo"))


def test_constraints_forbid_users_without_required_tags():
    assert not constraint_match({"required_tags": ("foo",)}, tagged_user("bar"))


def test_constraints_require_all_tags_to_be_matched():
    assert not constraint_match({"required_tags": ("foo", "bar")}, tagged_user("foo"))


def test_constraints_can_allow_irrelevant_tags_for_required():
    assert constraint_match({"required_tags": ("foo",)}, tagged_user("foo", "bar"))


def test_constraints_forbid_users_with_excluded_tags():
    assert not constraint_match({"excluded_tags": ("foo",)}, tagged_user("foo"))


def test_constraints_permit_users_without_excluded_tags():
    assert constraint_match({"excluded_tags": ("foo",)}, tagged_user("bar"))


def test_constraints_exclude_with_any_tags():
    assert not constraint_match({"excluded_tags": ("foo", "bar")}, tagged_user("foo"))


def test_constraints_raise_valueerror_for_unknown_keys():
    with pytest.raises(ValueError):
        Constraints.from_json({"foo": "bar"})


def test_not_disjoint_when_empty():
    assert is_disjoint({}, {}) is False


def test_disjoint_basic():
    assert is_disjoint({"required_tags": ("foo",)}, {"excluded_tags": ("foo",)})


def test_disjoint_swapped():
    assert is_disjoint({"excluded_tags": ("foo",)}, {"required_tags": ("foo",)})


def test_disjoint_when_shared_tag():
    assert is_disjoint(
        {"excluded_tags": ("foo",), "required_tags": ("bar",)},
        {"required_tags": ("foo", "bar")},
    )


def test_disjoint_when_shared_excluded_tag():
    assert is_disjoint(
        {"excluded_tags": ("foo", "bar")},
        {"required_tags": ("foo",), "excluded_tags": ("bar",)},
    )


def test_not_disjoint_when_sharing_tags():
    assert is_disjoint(
        {"required_tags": ("foo",), "excluded_tags": ("bar",)},
        {"required_tags": ("foo",), "excluded_tags": ("bar",)},
    ) is False


def test_constraints_explode_with_vim_and_vigour_if_given_a_dodgy_era():
    with pytest.raises(ValueError):
        Constraints(era="bees")


def test_not_disjoint_when_only_one_is_date_bounded():
    assert is_disjoint({"joined_after": "2018-05-01 00:00+0000"}, {}) is False


def test_not_disjoint_when_dates_are_both_bounded_on_same_side():
    assert is_disjoint(
        {"joined_after": "2018-05-01 00:00+0000"},
        {"joined_after": "2018-05-02 00:00+0000"},
    ) is False


def test_not_disjoint_when_one_sided_in_different_directions_and_overlapping():
    assert is_disjoint(
        {"joined_after": "2018-05-01 00:00+0000"},
        {"joined_before": "2018-05-02 00:00+0000"},
    ) is False


def test_disjoint_when_one_sided_in_different_directions_and_not_overlapping():
    assert is_disjoint(
        {"joined_after": "2018-05-02 00:00+0000"},
        {"joined_before": "2018-05-01 00:00+0000"},
    ) is True


def test_disjoint_when_one_sided_in_different_directions_and_not_overlapping_on_the_margin():
    assert is_disjoint(
        {"joined_after": "2018-05-01 00:00+0000"},
        {"joined_before": "2018-05-01 00:00+0000"},
    ) is True


def test_not_disjoint_when_doubly_bounded_and_overlapping():
    assert is_disjoint(
        {
            "joined_after": "2018-05-01 00:00+0000",
            "joined_before": "2018-05-03 00:00+0000",
        },
        {
            "joined_after": "2018-05-02 00:00+0000",
            "joined_before": "2018-05-04 00:00+0000",
        },
    ) is False


def test_not_disjoint_when_doubly_bounded_and_one_contains_the_other_wholly():
    assert is_disjoint(
        {
            "joined_after": "2018-05-01 00:00+0000",
            "joined_before": "2018-05-04 00:00+0000",
        },
        {
            "joined_after": "2018-05-02 00:00+0000",
            "joined_before": "2018-05-03 00:00+0000",
        },
    ) is False


def test_disjoint_when_doubly_bounded_and_actually_non_overlapping():
    assert is_disjoint(
        {
            "joined_after": "2018-05-01 00:00+0000",
            "joined_before": "2018-05-02 00:00+0000",
        },
        {
            "joined_after": "2018-05-03 00:00+0000",
            "joined_before": "2018-05-04 00:00+0000",
        },
    ) is True
