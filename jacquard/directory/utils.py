import pkg_resources


def open_directory(engine, kwargs):
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
