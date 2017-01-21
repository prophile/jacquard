import io
import textwrap
import contextlib
import unittest.mock

from jacquard.cli import main
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
