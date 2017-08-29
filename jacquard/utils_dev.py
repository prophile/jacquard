"""Utilities for dev commands."""

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

    while True:
        if isinstance(data, bool) and data:
            # Try setting bools to false
            return False if is_valid(False) else True
        elif isinstance(data, int) or isinstance(data, float):
            # Try setting numbers to 0, 1 or -1
            if is_valid(0):
                return 0
            elif is_valid(1):
                return 1
            elif is_valid(-1):
                return -1
            else:
                return data
        elif isinstance(data, str):
            if len(data) == 0:
                return data  # as minimal as it gets
            # Try the empty string
            if is_valid(''):
                return ''
            if is_valid(data[1:]):
                data = data[1:]
                continue
            if is_valid(data[:-1]):
                data = data[:-1]
                continue
            return data  # No further string shrinks
        elif isinstance(data, list):
            if len(data) == 0:
                return data  # as minimal as it gets
            # Try the empty list here
            if is_valid([]):
                return []
            # Try dropping the first element
            if is_valid(data[1:]):
                data = data[1:]
                continue
            # Try dropping the last element
            if is_valid(data[:-1]):
                data = data[:-1]
                continue
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
                data = output_elements
                continue
            else:
                return data
        elif isinstance(data, dict):
            if len(data) == 0:
                return data
            # First try the empty dict
            if is_valid({}):
                return {}

            # Drop keys and shrink values
            any_changes = False

            keys = list(data.keys)
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

            if not any_changes:
                return data
        else:
            # No shrink on this type
            return data
