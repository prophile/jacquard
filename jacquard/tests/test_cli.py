import io
import textwrap
import contextlib
import unittest.mock

import pytest

from jacquard.cli import CommandError, main
from jacquard.storage.dummy import DummyStore


def test_smoke_cli_help():
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(['--help'])
    except SystemExit:
        pass

    assert output.getvalue().startswith("usage: ")


def test_help_message_when_given_no_subcommand():
    try:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main([])
    except SystemExit:
        pass

    assert output.getvalue().startswith("usage: ")


def test_run_basic_command():
    config = unittest.mock.Mock()
    config.storage = DummyStore('', data={
        'foo': 'bar',
    })

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        main(['storage-dump'], config=config)

    assert output.getvalue().strip() == textwrap.dedent("""
        foo
        ===
        'bar'

        """
    ).strip()


def test_run_write_command():
    config = unittest.mock.Mock()
    config.storage = DummyStore('', data={})

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        main(['set-default', 'foo', '"bar"'], config=config)

    assert output.getvalue() == ''

    assert config.storage.data == {'defaults': '{"foo": "bar"}'}


def test_erroring_command():
    config = unittest.mock.Mock()

    ERROR_MESSAGE = "MOCK ERROR: Something went wrong in the"

    mock_parser = unittest.mock.Mock()
    mock_options = unittest.mock.Mock()
    mock_options.func = unittest.mock.Mock(
        side_effect=CommandError(ERROR_MESSAGE),
    )
    mock_parser.parse_args = unittest.mock.Mock(
        return_value=mock_options,
    )

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr), pytest.raises(SystemExit):
        with unittest.mock.patch(
            'jacquard.cli.argument_parser',
            return_value=mock_parser,
        ):
            main(['command'], config=config)

    assert stderr.getvalue() == ERROR_MESSAGE + "\n"
