from jacquard.utils_dev import shrink


def test_shrink_none_produces_none():
    assert shrink(None, lambda x: True) is None


def test_shrink_false_produces_false():
    assert shrink(False, lambda x: True) is False


def test_shrink_true_produces_false():
    assert shrink(True, lambda x: True) is False


def test_shrink_true_doesnt_drop_to_false_if_conditions_dont_permit():
    assert shrink(True, lambda x: x) is True


def test_numbers_shrink_to_zero():
    assert shrink(100, lambda x: True) == 0


def test_negatives_shrink_to_minus_one():
    assert shrink(-100, lambda x: x < 0) == -1


def test_negative_floats_shrink_to_minus_one():
    assert shrink(-100.0, lambda x: x < 0) == -1


def test_positives_shrink_to_one():
    assert shrink(100, lambda x: x > 0) == 1


def test_positive_floats_shrink_to_one():
    assert shrink(100.0, lambda x: x > 0) == 1


def test_numbers_do_not_shrink_if_they_cannot():
    assert shrink(100, lambda x: x == 100) == 100


def test_strings_shrink_to_empty():
    assert shrink("bees", lambda x: True) == ""


def test_strings_shrink_by_cutting_off_end():
    assert shrink("bees", lambda x: x.startswith("be")) == "be"


def test_strings_shrink_by_cutting_off_start():
    assert shrink("bees", lambda x: x.endswith("s")) == "s"


def test_strings_shrink_by_cutting_off_from_both_ends():
    assert shrink("bees", lambda x: "ee" in x) == "ee"


def test_unshrinkable_strings_are_not_shrunk():
    assert shrink("bees", lambda x: x == "bees") == "bees"


def test_strings_shrink_to_a_where_possible():
    assert shrink("bees", lambda x: len(x) >= 2) == "aa"


def test_empty_string_is_unshrunk():
    assert shrink("", lambda x: True) == ""


def test_empty_list_is_unshrunk():
    assert shrink([], lambda x: True) == []


def test_lists_shrunk_by_cutting_off_from_both_ends():
    assert shrink(list("bees"), lambda x: "ee" in "".join(x)) == ["e", "e"]


def test_lists_shrink_to_the_empty_list():
    assert shrink([1, 2, 3], lambda x: True) == []


def test_lists_shrink_down_sub_elements():
    assert (
        shrink([3, 3, 3], lambda x: len(x) == 3 and all(y > 0 for y in x))
        == [1, 1, 1]
    )


def test_empty_dict_is_unshrunk():
    assert shrink({}, lambda x: True) == {}


def test_dicts_shrink_to_the_empty_dict():
    assert shrink({"a": "b"}, lambda x: True) == {}


def test_dicts_are_shrunk_by_dropping_keys():
    assert shrink({"a": "", "c": ""}, lambda x: "a" in x) == {"a": ""}


def test_dicts_shrink_values():
    assert shrink({"a": 100}, lambda x: x.get("a", 0) > 0) == {"a": 1}


def test_unhandled_types_are_passed_through():

    def a_function():
        pass

    assert shrink(a_function, lambda x: True) is a_function
