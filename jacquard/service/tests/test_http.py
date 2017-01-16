import json

import datetime
import dateutil.tz

from unittest.mock import Mock

from jacquard.service import get_wsgi_app
from jacquard.storage.dummy import DummyStore
from jacquard.directory.base import UserEntry
from jacquard.directory.dummy import DummyDirectory

import werkzeug.test


def get(path):
    config = Mock()
    config.storage = DummyStore('', data={
        'defaults': {'pony': 'gravity'},
        'active-experiments': ['foo'],
        'experiments/foo': {
            'id': 'foo',
            'constraints': {
                'excluded_tags': ['excluded'],
                'anonymous': False,
            },
            'branches': [{'id': 'bar', 'settings': {'pony': 'horse'}}],
        },
    })
    now = datetime.datetime.now(dateutil.tz.tzutc())
    config.directory = DummyDirectory(users=(
        UserEntry(id=1, join_date=now, tags=('excluded',)),
        UserEntry(id=2, join_date=now, tags=('excluded',)),
        UserEntry(id=3, join_date=now, tags=()),
    ))

    wsgi = get_wsgi_app(config)
    test_client = werkzeug.test.Client(wsgi)

    data, status, headers = test_client.get(path)
    assert status == '200 OK'
    all_data = b''.join(data)
    return json.loads(all_data)


def test_root():
    assert get('/') == {
        'experiments': '/experiment',
        'user': '/users/<user>',
    }


def test_user_lookup():
    assert get('/users/1') == {
        'user': '1',
        'pony': 'gravity',
    }


def test_user_lookup_with_non_numeric_id():
    assert get('/users/bees') == {
        'user': 'bees',
        'pony': 'gravity',
    }


def test_experiments_list():
    # Verify no exceptions
    assert get('/experiment') == [{
        'id': 'foo',
        'url': '/experiment/foo',
        'state': 'active',
        'name': 'foo',
    }]


def test_experiment_get_smoke():
    # Verify no exceptions
    assert get('/experiment/foo')['name'] == 'foo'


def test_experiment_get_membership():
    assert get('/experiment/foo')['branches']['bar'] == [3]
