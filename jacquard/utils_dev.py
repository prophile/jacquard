"""Utilities for dev commands."""


def _shrink_bool(data, is_valid):
    # Attempt to reduce to False, if valid
    if data and is_valid(False):
        return False, False
    return data, False


def _shrink_none(data, is_valid):
    return None, False  # None is unshrinkable


def _shrink_number(data, is_valid):
    # Try setting numbers to 0, 1 or -1
    if is_valid(0):
        return 0, False
    elif is_valid(1):
        return 1, False
    elif is_valid(-1):
        return -1, False
    else:
        return data, False


def _shrink_string(data, is_valid):
    if len(data) == 0:
        return data, False  # as minimal as it gets
    # Try the empty string
    if is_valid(''):
        return '', False
    while is_valid(data[1:]):
        data = data[1:]
    while is_valid(data[:-1]):
        data = data[:-1]
    return data, False  # No further string shrinks


def _shrink_list(data, is_valid):
    if len(data) == 0:
        return data, False  # as minimal as it gets
    # Try the empty list here
    if is_valid([]):
        return [], False
    # Try dropping the first element
    while is_valid(data[1:]):
        data = data[1:]
    # Try dropping the last element
    while is_valid(data[:-1]):
        data = data[:-1]
    # Shrink each element
    any_shrunk = False
    output_elements = []
    for index, element in enumerate(data):
        def is_valid_child(substitution):
            data_copy = list(data)
            data_copy[index] = substitution
            return is_valid(data_copy)

        shrunk_element = shrink(element, is_valid_child)
        if shrunk_element != element:
            any_shrunk = True
        output_elements.append(shrunk_element)
    if any_shrunk:
        return output_elements, True
    else:
        return data, False


def _shrink_dict(data, is_valid):
    if len(data) == 0:
        return data, False
    # First try the empty dict
    if is_valid({}):
        return {}, False

    # Drop keys and shrink values
    any_changes = False

    keys = list(data.keys())
    keys.sort()

    for key in keys:
        # See if we can drop this key
        if is_valid({
                        dict_key: dict_value
                        for dict_key, dict_value in data.items()
                        if dict_key != key
                        }):
            del data[key]
            any_changes = True
        else:
            # We can't, try to shrink this key
            def is_valid_substitution(substitution):
                copied_data = dict(data)
                copied_data[key] = substitution
                return is_valid(copied_data)

            shrunk_value = shrink(
                data[key],
                is_valid_substitution,
            )

            if shrunk_value != data[key]:
                any_changes = True
                data[key] = shrunk_value

    return data, any_changes


_SHRINKERS = {
    type(None): _shrink_none,
    int: _shrink_number,
    float: _shrink_number,
    bool: _shrink_bool,
    str: _shrink_string,
    list: _shrink_list,
    tuple: _shrink_list,
    dict: _shrink_dict,
}


def shrink(data, is_valid):
    """
    Simplify `data` subject to `is_valid(data)`.

    `data` is any JSON-form data (strings, bools, None, ints, floats, lists,
    and dicts). This is roughly analogous to the concept of `shrink` from
    `QuickCheck`.

    It's used in `bugpoint`.
    """
    # This is in principle recursive, but we do this with explicit iteration
    # to save on stack space.

    any_changes = True
    while any_changes:
        try:
            shrinker = _SHRINKERS[type(data)]
        except KeyError:
            # Unshrinkable type
            return data
        data, any_changes = shrinker(data, is_valid)
    return data
