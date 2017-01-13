"""
User directories.

This subsystem is responsible for mapping user IDs, of whatever form they may
take, to join dates and tags. This is important for experiment constraints.

If you never use experiment constraints, feel free to use the provided "dummy"
directory engine. There is also a convenient "django" engine for users of
Django's `django.contrib.auth`, which uses sqlalchemy to query the `auth_user`
table. It has a single tag for superusers.

The system is pluggable by adding new entry points into the
`jacquard.directory_engines` group.
"""
from .utils import open_directory

__all__ = ('open_directory',)
