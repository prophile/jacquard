"""
Django user directory.

This directory pulls data from an `auth_user` SQL table corresponding with
Django's `django.contrib.auth` user model. It uses the integer ID field as
the assumed form of user ID.

Tags are limited - it only has one tag, `superuser`. For superusers.

Potentially useful for small Django projects, or as a superclass for a more
intricate Django user directory.
"""

import functools
import sqlalchemy
import sqlalchemy.sql

from .base import Directory, UserEntry


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
        self.engine = sqlalchemy.create_engine(url)

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

        result = self.engine.execute(
            sqlalchemy.sql.text(query),
            user=int(user_id),
        )

        try:
            row = next(iter(result))
        except StopIteration:
            return None

        return self.describe_user(row)

    def all_users(self):
        """
        Iterate over all users.

        For the sake of consistency this orders by the `id` field. Under most
        database configurations with Django the `id` field will have a unique
        BTree or equivalent index, so this shouldn't *drastically* add to the
        query runtime.

        Results are streamed in rather than forced.
        """
        query = self.query + " ORDER BY id ASC"

        result = self.engine.execute(query)

        for row in result:
            yield self.describe_user(row)
