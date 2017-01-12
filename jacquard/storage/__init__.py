import pkg_resources


def open_engine(engine, url):
    entry_point = None

    for candidate_entry_point in pkg_resources.iter_entry_points(
        'jacquard.storage_engines',
        name=engine,
    ):
        entry_point = candidate_entry_point

    if entry_point is None:
        raise RuntimeError("Cannot find storage engine '%s'" % engine)

    cls = entry_point.load()
    return cls(url)
