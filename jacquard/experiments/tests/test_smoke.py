from unittest.mock import Mock

from jacquard.cli import main
from jacquard.storage.dummy import DummyStore


def test_launch():
    config = Mock()
    config.storage = DummyStore('', data={
        'experiments/foo': {
            'branches': [
                {
                    'id': 'bar',
                    'settings': {},
                },
            ],
        },
    })

    main(('launch', 'foo'), config=config)

    assert 'launched' in config.storage['experiments/foo']
    assert 'foo' in config.storage['active-experiments']
