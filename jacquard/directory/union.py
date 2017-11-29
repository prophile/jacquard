"""
Union directory.

This is a specialised pseudo-directory which combines other directories to
give an opaque union of them.

An example use case is where there are two classes of user - say, permanent
users identified by ID and transient users identified by session ID - who are
looked up in distinct ways but where both are targets for testing.
"""

import re
import collections

from jacquard.directory.base import Directory
from jacquard.directory.utils import open_directory

INDEXED_KEY_RE = re.compile(r'^([^\[]+)\[([0-9]+)]$')


class UnionDirectory(Directory):
    """A union of zero or more directories."""

    def __init__(self, subdirectories):
        """
        Initializer.

        This is used with an iterable of `Directory` instances to construct
        directly: `from_configuration` is used for the format as found in
        `jacquard.cfg` files.
        """
        self._subdirectories = list(subdirectories)

    @classmethod
    def _construct_subdirectories_from_config(cls, config, options):
        # The configuration format is config_key[index] = value.
        # We extract this in three logical stages:
        # (1) Calculate the maximum index,
        # (2) Construct the dict of indices -> configurations,
        # (3) Call `open_directory` on each.
        # For the sake of simplicitly steps (1) and (2) are combined using
        # some defaultdict trickery.
        sub_configurations = collections.defaultdict(dict)

        for key, value in options.items():
            match = INDEXED_KEY_RE.match(key)

            if match is None:
                continue

            config_key = match.group(1)
            config_index = int(match.group(2))

            sub_configurations[config_index][config_key] = value

        try:
            maximum_index = max(sub_configurations.keys())
        except ValueError:
            # No configurations at all: this is a null union
            return

        for subdirectory_index in range(maximum_index + 1):
            sub_configuration = sub_configurations[subdirectory_index]
            engine = sub_configuration.pop('engine')
            yield open_directory(config, engine, sub_configuration)

    @classmethod
    def from_configuration(cls, config, options):
        """
        Build from the configuration format.

        This lists configuration for the subdirectories with square bracket
        indexing. For example:

            [directory]
            engine = union
            engine[0] = my_engine
            param[0] = my_param
            engine[1] = django
            url[1] = postgresql:///my_django_db
        """
        return cls(cls._construct_subdirectories_from_config(config, options))

    def lookup(self, user_id):
        """
        Look up user by ID.

        For missing users this must return None, otherwise it must return a
        corresponding `UserEntry`.

        Where a user is present in multiple subdirectories, the first is
        taken.
        """
        for subdirectory in self._subdirectories:
            user_entry = subdirectory.lookup(user_id)

            if user_entry is not None:
                return user_entry

        return None
