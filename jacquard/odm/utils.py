"""Misc utils for ODM use."""

import functools


def method_dispatch(fn):
    """
    Version of `functools.singledispatch` suitable for use in methods.

    Essentially identical to `singledispatch` but switching on the type of the
    second argument rather than the first since the first will be `self`.
    """
    dispatcher = functools.singledispatch(fn)

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            dispatch_type = args[0].__class__
        except (LookupError, AttributeError):
            dispatch_type = object
        return dispatcher.dispatch(dispatch_type)(self, *args, **kwargs)

    wrapper.register = dispatcher.register
    return wrapper
