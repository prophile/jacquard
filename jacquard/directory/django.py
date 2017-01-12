import functools
import sqlalchemy
import sqlalchemy.sql

from .base import Directory, UserEntry


class DjangoDirectory(Directory):
    query = """
    SELECT
        auth_user.id,
        auth_user.date_joined,
        auth_user.is_superuser
    FROM
        auth_user
    """

    def __init__(self, url):
        self.engine = sqlalchemy.create_engine(url)

    def describe_user(self, row):
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
        query = self.query + " ORDER BY id ASC"

        result = self.engine.execute(query)

        for row in result:
            yield self.describe_user(row)
