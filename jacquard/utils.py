"""General utility functions."""


import difflib


def check_keys(passed_keys, known_keys):
    """
    Validate that all elements of passed_keys are in known_keys.

    Raises ValueError if not.

    Also makes the error message useful.
    """
    # Upfront conversion to set in case the iterable is not re-usable
    known_keys = set(known_keys)

    unknown_keys = set(passed_keys) - known_keys

    if not unknown_keys:
        return

    if len(unknown_keys) > 1:
        raise ValueError("Unknown keys: %s" % ", ".join(sorted(unknown_keys)))

    (unknown_key,) = unknown_keys

    close_matches = difflib.get_close_matches(unknown_key, known_keys)

    if not close_matches:
        raise ValueError("Unknown key: %s" % unknown_key)

    if len(close_matches) == 1:
        (close_match,) = close_matches
        raise ValueError("Unknown key: %s (did you mean %s?)" % (
            unknown_key,
            close_match,
        ))

    raise ValueError("Unknown key: %s (close matches: %s)" % (
        unknown_key,
        ", ".join(close_matches),
    ))
