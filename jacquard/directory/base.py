"""Base class for directory implementations."""

import abc
import collections


UserEntry = collections.namedtuple('UserEntry', 'id join_date tags')


class Directory(metaclass=abc.ABCMeta):
    """User directory."""

    @abc.abstractmethod
    def __init__(self, **kwargs):
        """
        Standard constructor.

        Keyword arguments are taken from the `directory` section of config
        files, and appear as strings. Useful for specifying connection URLs
        etc.
        """

    @abc.abstractmethod
    def lookup(self, user_id):
        """
        Look up user by ID.

        For missing users this must return None, otherwise it must return a
        corresponding `UserEntry`.
        """
        pass

    @abc.abstractmethod
    def all_users(self):
        """
        Iterable over all known users.

        Represented as `UserEntry` instances.
        """
        pass
