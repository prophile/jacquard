import json
import datetime
from unittest.mock import Mock

import pytest
import dateutil.tz
import werkzeug.http
import werkzeug.test
from werkzeug.datastructures import MultiDict

from jacquard.service import get_wsgi_app
from jacquard.storage.dummy import DummyStore
from jacquard.directory.base import UserEntry
from jacquard.directory.dummy import DummyDirectory


def get_test_client():
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
    return werkzeug.test.Client(wsgi)


def get_status(path):
    data, status, headers = get_test_client().get(path)
    all_data = b''.join(data)
    return status, all_data


def get(path):
    status, all_data = get_status(path)
    assert status == '200 OK'
    return json.loads(all_data.decode('utf-8'))


def post(path, form):
    client = get_test_client()
    data, status, headers = client.post(path, data=form)
    assert status == '200 OK'
    return json.loads(b''.join(data).decode('utf-8'))


def test_root():
    assert get('/') == {
        'experiments': '/experiments',
        'users': '/users/:user',
        'defaults': '/defaults',
    }


def test_root_accept_json():
    client = get_test_client()
    data, status, headers = client.get(
        '/',
        headers={'Accept': 'application/json'},
    )
    assert status == '200 OK'
    assert headers.get('Content-Type') == 'application/json'


def test_root_invalid_accept_returns_406():
    client = get_test_client()
    data, status, headers = client.get(
        '/',
        headers={'Accept': 'text/not-a-real-mime-type'},
    )
    assert status == '406 Not Acceptable'


def test_root_accept_with_bad_charset_returns_406():
    client = get_test_client()
    data, status, headers = client.get(
        '/',
        headers={'Accept': 'text/plain', 'Accept-Charset': 'not-a-real-charset'},
    )
    assert status == '406 Not Acceptable'


@pytest.mark.parametrize('mime', [
    'text/plain',
    'application/x-yaml',
    'text/x-yaml',
    'text/html',
])
def test_root_accept_on_alternative_content_type(mime):
    client = get_test_client()
    data, status, headers = client.head(
        '/',
        headers={'Accept': mime},
    )

    assert status == '200 OK'

    content_type, _ = werkzeug.http.parse_options_header(
        headers['Content-Type'],
    )
    assert content_type == mime


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
    assert get('/experiments') == [{
        'id': 'foo',
        'url': '/experiments/foo',
        'state': 'active',
        'name': 'foo',
    }]


def test_experiment_get_smoke():
    # Verify no exceptions
    assert get('/experiments/foo')['name'] == 'foo'


def test_experiment_get_branches():
    assert set(get('/experiments/foo')['branches']) == {'bar'}


def test_missing_paths_get_404():
    assert get_status('/missing')[0] == '404 NOT FOUND'


def test_get_on_experiment_partition_gets_405():
    assert (
        get_status('/experiments/foo/partition')[0] ==
        '405 METHOD NOT ALLOWED'
    )


def test_experiment_partition():
    params = MultiDict([
        ('u', '1'),
        ('u', '2'),
        ('u', '3'),
        ('u', '4'),
    ])
    result = post('/experiments/foo/partition', params)
    assert set(result['branches'].keys()) == {'bar'}
