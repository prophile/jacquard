import pkg_resources


def plug_all(group):
    entry_points_group = 'jacquard.%s' % group

    for entry_point in pkg_resources.iter_entry_points(entry_points_group):
        yield entry_point.name, entry_point.resolve


def plug(group, name=None):
    candidate = None

    for point_name, resolver in plug_all(group):
        if point_name != name:
            continue

        candidate = resolver

    if candidate is None:
        raise RuntimeError("Could not find plugin for '%s'" % name)

    return candidate
