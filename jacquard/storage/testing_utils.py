"""Misc utils for use in storage tests."""

import hypothesis
import hypothesis.strategies

arbitrary_json = hypothesis.strategies.recursive(
    hypothesis.strategies.floats(allow_nan=False, allow_infinity=False) |
    hypothesis.strategies.booleans() |
    hypothesis.strategies.text() |
    hypothesis.strategies.none(),
    lambda children: (
        hypothesis.strategies.lists(children) |
        hypothesis.strategies.dictionaries(
            hypothesis.strategies.text(),
            children,
        )
    ),
    max_leaves=10,
).filter(lambda x: x is not None)
arbitrary_key = hypothesis.strategies.text()
