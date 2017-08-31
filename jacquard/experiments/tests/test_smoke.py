import io
import copy
import datetime
import contextlib
from unittest.mock import Mock, patch

import pytest
import dateutil.tz

from jacquard.cli import main, _build_argument_parser
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


@contextlib.contextmanager
def _disable_argparse_cache():
    _build_argument_parser.cache_clear()
    try:
        yield
    finally:
        _build_argument_parser.cache_clear()


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
    assert 'foo' in config.storage['concluded-experiments']
    assert not config.storage['defaults']


def test_conclude_updates_defaults():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)

    main(('conclude', 'foo', 'bar'), config=config)

    assert 'concluded' in config.storage['experiments/foo']
    assert 'foo' not in config.storage['active-experiments']
    assert 'foo' in config.storage['concluded-experiments']
    assert config.storage['defaults'] == BRANCH_SETTINGS


def test_load_after_launch_errors():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)

    experiment_data = {'id': 'foo'}
    experiment_data.update(DUMMY_DATA_PRE_LAUNCH['experiments/foo'])

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr), pytest.raises(SystemExit):
        with patch(
            'jacquard.experiments.commands.yaml.safe_load',
            return_value=experiment_data,
        ), patch(
            'jacquard.experiments.commands.argparse.FileType',
            return_value=str,
        ):
            main(('load-experiment', 'foo.yaml'), config=config)

    stderr_content = stderr.getvalue()
    assert "Experiment 'foo' is live, refusing to edit" in stderr_content

    fresh_data = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)
    assert fresh_data.data == config.storage.data, "Data should be unchanged"


def test_load_after_launch_with_skip_launched():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)

    experiment_data = {'id': 'foo'}
    experiment_data.update(DUMMY_DATA_PRE_LAUNCH['experiments/foo'])

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr), patch(
        'jacquard.experiments.commands.yaml.safe_load',
        return_value=experiment_data,
    ), patch(
        'jacquard.experiments.commands.argparse.FileType',
        return_value=str,
    ), _disable_argparse_cache():
        main(('load-experiment', '--skip-launched', 'foo.yaml'), config=config)

    fresh_data = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)
    assert fresh_data.data == config.storage.data, "Data should be unchanged"

    stderr_content = stderr.getvalue()
    assert '' == stderr_content


def test_load_after_conclude_errors():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)

    main(('conclude', 'foo', 'bar'), config=config)
    original_data = copy.deepcopy(config.storage.data)

    experiment_data = {'id': 'foo'}
    experiment_data.update(DUMMY_DATA_PRE_LAUNCH['experiments/foo'])

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr), pytest.raises(SystemExit):
        with patch(
            'jacquard.experiments.commands.yaml.safe_load',
            return_value=experiment_data,
        ), patch(
            'jacquard.experiments.commands.argparse.FileType',
            return_value=str,
        ), _disable_argparse_cache():
            main(('load-experiment', 'foo.yaml'), config=config)

    assert original_data == config.storage.data, "Data should be unchanged"

    stderr_content = stderr.getvalue()
    assert "Experiment 'foo' has concluded, refusing to edit" in stderr_content


def test_load_after_conclude_with_skip_launched():
    config = Mock()
    config.storage = DummyStore('', data=DUMMY_DATA_POST_LAUNCH)

    main(('conclude', 'foo', 'bar'), config=config)
    original_data = copy.deepcopy(config.storage.data)

    experiment_data = {'id': 'foo'}
    experiment_data.update(DUMMY_DATA_PRE_LAUNCH['experiments/foo'])

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr), patch(
        'jacquard.experiments.commands.yaml.safe_load',
        return_value=experiment_data,
    ), patch(
        'jacquard.experiments.commands.argparse.FileType',
        return_value=str,
    ), _disable_argparse_cache():
        main(('load-experiment', '--skip-launched', 'foo.yaml'), config=config)

    assert original_data == config.storage.data, "Data should be unchanged"

    stderr_content = stderr.getvalue()
    assert '' == stderr_content
