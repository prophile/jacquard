from jacquard.directory.base import UserEntry
from jacquard.directory.django import DjangoDirectory

import pytest
import unittest.mock

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None


if sqlalchemy is not None:
    test_database = sqlalchemy.create_engine('sqlite://')
    test_database.execute("""
    CREATE TABLE auth_user(
        id INTEGER NOT NULL PRIMARY KEY,
        date_joined DATETIME NOT NULL,
        is_superuser BOOLEAN NOT NULL
    )
    """)

    test_database.execute("""
    INSERT INTO auth_user(id, date_joined, is_superuser) VALUES
        (1, date('now'), 1),
        (2, date('now'), 0),
        (3, date('now'), 0)
    """)


@pytest.mark.skipif(
    sqlalchemy is None,
    reason="sqlalchemy not installed",
)
@unittest.mock.patch('sqlalchemy.create_engine', lambda *args: test_database)
def test_get_extant_user():
    directory = DjangoDirectory('')

    user_one = directory.lookup('1')

    assert list(user_one.tags) == ['superuser']


@pytest.mark.skipif(
    sqlalchemy is None,
    reason="sqlalchemy not installed",
)
@unittest.mock.patch('sqlalchemy.create_engine', lambda *args: test_database)
def test_get_missing_user():
    directory = DjangoDirectory('')

    user_zero = directory.lookup('0')

    assert user_zero is None


@pytest.mark.skipif(
    sqlalchemy is None,
    reason="sqlalchemy not installed",
)
@unittest.mock.patch('sqlalchemy.create_engine', lambda *args: test_database)
def test_get_all_users():
    directory = DjangoDirectory('')

    users = directory.all_users()

    assert [x.id for x in users] == [1, 2, 3]
