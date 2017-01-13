"""User directory miscellaneous utilities."""

import pkg_resources


def open_directory(engine, kwargs):
    """
    Open a given directory, with engine and kwargs.

    Looks up the directory through the `jacquard.directory_engines` entry
    point group and instantiates the given class with `**kwargs`.
    """
    entry_point = None

    for candidate_entry_point in pkg_resources.iter_entry_points(
        'jacquard.directory_engines',
        name=engine,
    ):
        entry_point = candidate_entry_point

    if entry_point is None:
        raise RuntimeError("Cannot find directory engine '%s'" % engine)

    cls = entry_point.load()
    return cls(**kwargs)
