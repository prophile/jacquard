import functools


def method_dispatch(fn):
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
