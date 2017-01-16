import datetime
import dateutil.tz

from unittest.mock import Mock

from jacquard.cli import main
from jacquard.storage.dummy import DummyStore


BRANCH_SETTINGS = {'pony': 'gravity'}

DUMMY_DATA_PRE_LAUNCH = {
    'experiments/foo': {
        'branches': [
            {'id': 'bar', 'settings': BRANCH_SETTINGS},
        ],
    },
}

DUMMY_DATA_POST_LAUNCH = {
    'experiments/foo': {
        'branches': [
            {'id': 'bar', 'settings': BRANCH_SETTINGS},
        ],
        'launched': str(datetime.datetime.now(dateutil.tz.tzutc())),
    },
    'active-experiments': ['foo'],
}


def test_launch():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_PRE_LAUNCH)

    main(('launch', 'foo'), config=config)

    assert 'launched' in config.storage['experiments/foo']
    assert 'concluded' not in config.storage['experiments/foo']
    assert 'foo' in config.storage['active-experiments']


def test_conclude_no_branch():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)

    main(('conclude', 'foo', '--no-promote-branch'), config=config)

    assert 'concluded' in config.storage['experiments/foo']
    assert 'foo' not in config.storage['active-experiments']
    assert not config.storage['defaults']


def test_conclude_updates_defaults():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)

    main(('conclude', 'foo', 'bar'), config=config)

    assert 'concluded' in config.storage['experiments/foo']
    assert 'foo' not in config.storage['active-experiments']
    assert config.storage['defaults'] == BRANCH_SETTINGS
