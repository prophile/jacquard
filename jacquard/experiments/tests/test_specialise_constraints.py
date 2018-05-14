from unittest.mock import Mock

from jacquard.cli import main
from jacquard.storage import DummyStore


DUMMY_DATA_PRE_LAUNCH = {
    'experiments/foo': {
        'branches': [
            {'id': 'bar', 'settings': {'key': 'value'}},
        ],
        'constraints': {
            'era': 'new',
        },
    },
}


def test_constraints_are_specialised_on_launch():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_PRE_LAUNCH)

    main(('launch', 'foo'), config=config)

    bucket_zero = config.storage['buckets/0']
    (name, settings, constraints) = bucket_zero['entries'][0]

    assert 'era' not in constraints
