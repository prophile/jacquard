"""
Django user directory.

This directory pulls data from an `auth_user` SQL table corresponding with
Django's `django.contrib.auth` user model. It uses the integer ID field as
the assumed form of user ID.

Tags are limited - it only has one tag, `superuser`. For superusers.

Potentially useful for small Django projects, or as a superclass for a more
intricate Django user directory.
"""

import logging
import functools

import sqlalchemy
import sqlalchemy.sql

from .base import Directory, UserEntry

LOGGER = logging.getLogger('jacquard.directory.django')


class DjangoDirectory(Directory):
    """Django user directory."""

    query = """
    SELECT
        auth_user.id,
        auth_user.date_joined,
        auth_user.is_superuser
    FROM
        auth_user
    """

    def __init__(self, url):
        """Initialise with SQLAlchemy connection URL."""
        LOGGER.debug("Opening SQL connection to: %r", url)
        self.engine = sqlalchemy.create_engine(url)
        LOGGER.debug("(opened)")

    def describe_user(self, row):
        """
        Describe a user from a single row of results.

        This is intended to be overridden in subclasses which have provided a
        custom `query` in order to add more tags, or use a different notion of
        join date.
        """
        tags = []

        if row.is_superuser:
            tags.append('superuser')

        return UserEntry(
            id=row.id,
            join_date=row.date_joined,
            tags=tuple(tags),
        )

    @functools.lru_cache(maxsize=1024)
    def lookup(self, user_id):
        """
        Look up user by ID.

        This makes a single DB query (based on the `query` attribute with an
        added WHERE clause), with a small LRU cache applied on top.
        """
        query = self.query + " WHERE id = :user"

        try:
            user_id = int(user_id)
        except ValueError:
            LOGGER.debug("Invalid ID")
            return None

        LOGGER.debug("Lookup user %s", user_id)
        result = self.engine.execute(
            sqlalchemy.sql.text(query),
            user=user_id,
        )

        try:
            row = next(iter(result))
        except StopIteration:
            LOGGER.debug("not found")
            return None

        LOGGER.debug("Got row: %s", row)
        return self.describe_user(row)
