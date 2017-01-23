"""Plugin-loading subsystem."""

import sys
import logging
import functools

import pkg_resources

DEFAULT_PLUGIN_DIRECTORY = '/etc/jacquard/plugins'
LOGGER = logging.getLogger('jacquard.plugin')


def plug_all(group, config=None):
    """
    Load all plugins within a given group.

    Currently, this enumerates through entry points in the `jacquard.<group>`
    group.

    Returns an iterable of `(name, plugin)` pairs. Plugins are callables
    which, when called, load the actual plugin and return it.
    """
    LOGGER.debug("Enumerating plugins in group %s", group)

    # Add /etc/jacquard/plugins to the search path if not already there
    if DEFAULT_PLUGIN_DIRECTORY not in sys.path:
        sys.path.append(DEFAULT_PLUGIN_DIRECTORY)
        pkg_resources.working_set.add_entry(DEFAULT_PLUGIN_DIRECTORY)

    entry_points_group = 'jacquard.%s' % group

    for entry_point in pkg_resources.iter_entry_points(entry_points_group):
        yield entry_point.name, entry_point.load

    if config is not None:
        config_section = config.get('plugins:%s' % group, {})

        for key, value in config_section.items():
            entry_point_line = '%s = %s' % (key, value)

            entry_point = pkg_resources.EntryPoint.parse(entry_point_line)
            yield entry_point.name, entry_point.resolve


def plug(group, name, config=None):
    """
    Load a specific named plugin from the given group.

    In case of conflict, later plugins are given precedence as a means of
    plugin overriding.

    If no matching plugin is found a RuntimeError is raised.

    As with `plug_all` the returned plugin is lazy: a callable which, when
    called, actually loads and instantiates the plugin.
    """
    candidate = None

    for point_name, resolver in plug_all(group, config=config):
        if point_name != name:
            continue

        candidate = resolver

    if candidate is None:
        raise RuntimeError("Could not find plugin for '%s'" % name)

    @functools.wraps(candidate)
    def wrapped_loader(*args, **kwargs):
        LOGGER.info("Loaded %s plugin %r", group, name)
        return candidate(*args, **kwargs)

    return wrapped_loader
